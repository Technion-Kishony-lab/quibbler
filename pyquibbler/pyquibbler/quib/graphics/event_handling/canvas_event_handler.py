from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Optional, Tuple, Callable, Union

from matplotlib.artist import Artist
from matplotlib.backend_bases import MouseEvent, PickEvent, MouseButton
from matplotlib.axes import Axes

from pyquibbler.debug_utils.timer import timeit
from pyquibbler.env import END_DRAG_IMMEDIATELY

from .. import artist_wrapper
from ..redraw import end_dragging
from ..event_handling import graphics_inverse_assigner

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


GRAPHICS_ASSIGNMENT_MODE_AXES: Optional[Axes] = None


@contextmanager
def graphics_assignment_mode(axes: Axes):
    """
    In graphics assignment mode. Indicating the axes invoking the assignment.
    """

    global GRAPHICS_ASSIGNMENT_MODE_AXES
    GRAPHICS_ASSIGNMENT_MODE_AXES = axes
    try:
        yield
    finally:
        GRAPHICS_ASSIGNMENT_MODE_AXES = None


def get_graphics_assignment_mode_axes() -> Optional[Axes]:
    return GRAPHICS_ASSIGNMENT_MODE_AXES


def is_within_graphics_assignment_mode() -> bool:
    return GRAPHICS_ASSIGNMENT_MODE_AXES is not None


class CanvasEventHandler:
    """
    Handles all events from the canvas (such as press, drag, and pick), inverse assigning to the relevant quibs
    using a specific graphics inverse assignment function handler
    """
    CANVASES_TO_TRACKERS = {}

    @classmethod
    def get_or_create_initialized_event_handler(cls, canvas):
        if canvas in cls.CANVASES_TO_TRACKERS:
            return cls.CANVASES_TO_TRACKERS[canvas]

        self = cls(canvas=canvas)
        cls.CANVASES_TO_TRACKERS[canvas] = self
        self.initialize()

        return self

    def __init__(self, canvas):
        self.canvas = canvas
        self.current_pick_event: Optional[PickEvent] = None
        self.current_pick_quib: Optional[Quib] = None
        self._previous_mouse_event: Optional[MouseEvent] = None
        self._assignment_lock = Lock()

        self.EVENT_HANDLERS = {
            'button_press_event': self._handle_button_press,
            'button_release_event': self._handle_button_release,
            'motion_notify_event': self._handle_motion_notify,
            'pick_event': self._handle_pick_event
        }

    @staticmethod
    def _call_object_rightclick_callback_if_exists(obj: Union[Axes, Artist], mouse_event) -> bool:
        on_rightclick = getattr(obj, '_quibbler_on_rightclick', None)
        has_rightclick_callback = on_rightclick is not None
        if has_rightclick_callback:
            on_rightclick(mouse_event)

        return has_rightclick_callback

    def _handle_button_press(self, mouse_event: MouseEvent):
        if mouse_event.button is MouseButton.RIGHT:
            self._call_object_rightclick_callback_if_exists(mouse_event.inaxes, mouse_event)

    def _handle_button_release(self, _mouse_event: MouseEvent):
        end_dragging()
        self.current_pick_event = None
        self.current_pick_quib = None
        self._previous_mouse_event = None

    def _handle_pick_event(self, pick_event: PickEvent):
        self.current_pick_event = pick_event
        self.current_pick_quib = artist_wrapper.get_creating_quib(pick_event.artist)
        if pick_event.mouseevent.button is MouseButton.RIGHT:
            if not self._call_object_rightclick_callback_if_exists(pick_event.artist, pick_event.mouseevent):
                self._inverse_from_mouse_event(pick_event.mouseevent)

    def _inverse_assign_graphics(self, mouse_event: MouseEvent):
        """
        Reverse any relevant quibs in artists creation args
        """
        # We record the current pick_event to avoid a race condition when calling inverse_assign_drawing_func
        pick_event = self.current_pick_event
        if pick_event is None:
            # This case was observed in the wild
            return

        drawing_quib = self.current_pick_quib
        with timeit("motion_notify", "motion notify"), graphics_assignment_mode(mouse_event.inaxes):
            graphics_inverse_assigner.inverse_assign_drawing_func(
                func_args_kwargs=drawing_quib.handler.func_args_kwargs,
                mouse_event=mouse_event,
                pick_event=pick_event)

    def _inverse_assign_axis_limits(self,
                                    drawing_func: Callable,
                                    set_lim_quib: Quib,
                                    lim: Tuple[float, float],
                                    is_override_removal: bool = False,
                                    ):
        """
        Reverse axis limit change
        """
        with timeit("axis_lim_notify", "axis-lim notify"), graphics_assignment_mode(set_lim_quib.args[0]):
            graphics_inverse_assigner.inverse_assign_axes_lim_func(
                args=set_lim_quib.args,
                lim=lim,
                is_override_removal=is_override_removal,
            )

    @contextmanager
    def _try_acquire_assignment_lock(self):
        """
        A context manager that tries to acquire the assignment lock without blocking and returns
        whether it had succeeded or not.
        """
        locked = self._assignment_lock.acquire(blocking=False)
        try:
            yield locked
        finally:
            if locked:
                self._assignment_lock.release()

    def _handle_motion_notify(self, mouse_event: MouseEvent):
        self._inverse_from_mouse_event(mouse_event)

    def _inverse_from_mouse_event(self, mouse_event):
        if self.current_pick_event is not None:
            with self._try_acquire_assignment_lock() as locked:
                if locked:
                    # If not locked, there is already another motion handler running, we just drop this one.
                    # This could happen if changes are slow or if a dialog is open
                    if self._previous_mouse_event is None:
                        xy_dominance = None
                    else:
                        xy_dominance = 'x' if abs(mouse_event.x - self._previous_mouse_event.x) > \
                                              abs(mouse_event.y - self._previous_mouse_event.y) else 'y'
                    mouse_event.xy_dominance = xy_dominance
                    self._inverse_assign_graphics(mouse_event)
                    self._previous_mouse_event = mouse_event
                    if END_DRAG_IMMEDIATELY:
                        self.current_pick_event = None
                        self.current_pick_quib = None

    def initialize(self):
        """
        Initializes the canvas events handler to receive events from the canvas
        """
        handler_ids = []
        for event_type, handler in self.EVENT_HANDLERS.items():
            handler_ids.append(self.canvas.mpl_connect(event_type, handler))

        def disconnect(event):
            for handler_id in handler_ids:
                self.canvas.mpl_disconnect(handler_id)

            self.CANVASES_TO_TRACKERS.pop(self.canvas)

            for ax in self.canvas.figure.axes:
                ax.cla()

        handler_ids.append(self.canvas.mpl_connect('close_event', disconnect))

    def handle_axes_drag_pan(self, ax: Axes, drawing_func: Callable, lim: Tuple[float, float]):
        """
        This method is called by the overridden set_xlim, set_ylim
        """
        name = drawing_func.__name__
        set_lim_quib = artist_wrapper.get_setter_quib(ax, name)
        from pyquibbler.quib.quib import Quib
        if isinstance(set_lim_quib, Quib):
            with self._try_acquire_assignment_lock() as locked:
                if locked:
                    self._inverse_assign_axis_limits(
                        drawing_func=drawing_func,
                        set_lim_quib=set_lim_quib,
                        lim=lim,
                        is_override_removal=False,
                    )
        else:
            drawing_func(ax, lim)
