from contextlib import contextmanager
from threading import Lock
from typing import Optional, Tuple, Callable
from matplotlib.backend_bases import MouseEvent, PickEvent, MouseButton

from pyquibbler.env import END_DRAG_IMMEDIATELY
from pyquibbler.graphics import pressed, released
from pyquibbler.logger import logger
from pyquibbler.quib.graphics.redraw import end_dragging
from pyquibbler.utilities.performance_utils import timer
from pyquibbler.quib.graphics.event_handling import graphics_inverse_assigner
from pyquibbler.quib.graphics import artist_wrapper

from matplotlib.axes import Axes
from pyquibbler.quib import Quib


GRAPHICS_ASSIGNMENT_MODE_AXES: Optional[Axes] = None


@contextmanager
def graphics_assignment_mode(axes: Axes):
    """
    In graphics assinment mode. Indicating the axes invoking the assignment.
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
        self._assignment_lock = Lock()

        self.EVENT_HANDLERS = {
            'button_press_event': self._handle_button_press,
            'button_release_event': self._handle_button_release,
            'motion_notify_event': self._handle_motion_notify,
            'pick_event': self._handle_pick_event
        }

    def _handle_button_press(self, _mouse_event: MouseEvent):
        pressed()

    def _handle_button_release(self, _mouse_event: MouseEvent):
        if self.current_pick_event is not None:
            end_dragging()
        self.current_pick_event = None
        self.current_pick_quib = None
        released()

    def _handle_pick_event(self, pick_event: PickEvent):
        self.current_pick_event = pick_event
        self.current_pick_quib = artist_wrapper.get_creating_quib(pick_event.artist)
        if pick_event.mouseevent.button is MouseButton.RIGHT:
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
        with timer("motion_notify", lambda x: logger.info(f"motion notify {x}")), \
                graphics_assignment_mode(mouse_event.inaxes):
            graphics_inverse_assigner.inverse_assign_drawing_func(drawing_func=drawing_quib.func,
                                                                  args=drawing_quib.args,
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
        with timer("axis_lim_notify", lambda x: logger.info(f"axis-lim notify {x}")), \
                graphics_assignment_mode(set_lim_quib.args[0]):
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
                    self._inverse_assign_graphics(mouse_event)
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

    def handle_axes_limits_changed(self, ax: Axes, drawing_func: Callable, lim: Tuple[float, float]):
        """
        This method is called by the overridden set_xlim, set_ylim
        """
        name = drawing_func.__name__
        set_lim_quib = artist_wrapper.get_setter_quib(ax, name)
        if isinstance(set_lim_quib, Quib):
            with self._try_acquire_assignment_lock() as locked:
                if locked:
                    self._inverse_assign_axis_limits(
                        drawing_func=drawing_func,
                        set_lim_quib=set_lim_quib,
                        lim=lim,
                        is_override_removal=False,
                    )
