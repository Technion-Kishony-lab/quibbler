from __future__ import annotations

import weakref
from contextlib import contextmanager
from threading import Lock
from typing import Optional, Tuple, Callable, Union

from matplotlib.artist import Artist
from matplotlib.backend_bases import MouseEvent, PickEvent, MouseButton, FigureCanvasBase
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from pyquibbler.debug_utils.timer import timeit
from pyquibbler.env import END_DRAG_IMMEDIATELY
from .enhance_pick_event import EnhancedPickEventWithFuncArgsKwargs

from .. import artist_wrapper
from ..artist_wrapper import clear_all_quibs
from ..redraw import end_dragging, start_dragging
from ..event_handling import graphics_inverse_assigner
from ..graphics_assignment_mode import graphics_assignment_mode

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


def _get_all_axs_from_figure(figure: Figure):
    return figure.get_axes()


def _get_all_artists_from_axes(ax: Axes):
    return ax.get_children()


def _get_all_artists_from_axes_of_figure(figure: Figure):
    axs = _get_all_axs_from_figure(figure)
    all_artists = axs
    for ax in axs:
        all_artists.extend(_get_all_artists_from_axes(ax))
    return all_artists


class CanvasEventHandler:
    """
    Handles all events from the canvas (such as press, drag, and pick), inverse assigning to the relevant quibs
    using a specific graphics inverse assignment function handler
    """
    CANVASES_TO_TRACKERS = weakref.WeakValueDictionary()

    @classmethod
    def get_or_create_initialized_event_handler(cls, canvas):
        if canvas in cls.CANVASES_TO_TRACKERS:
            return cls.CANVASES_TO_TRACKERS[canvas]

        self = cls(canvas=canvas)
        cls.CANVASES_TO_TRACKERS[canvas] = self
        self.initialize()

        return self

    def __init__(self, canvas: FigureCanvasBase):
        self.canvas = canvas
        self.enhanced_pick_event: Optional[EnhancedPickEventWithFuncArgsKwargs] = None
        self._assignment_lock = Lock()
        self._handler_ids = []
        self._original_destroy = None

        self.EVENT_HANDLERS = {
            'button_press_event': self._handle_button_press,
            'button_release_event': self._handle_button_release,
            'motion_notify_event': self._handle_motion_notify,
            'pick_event': self._handle_pick_event,
            'close_event': self.disconnect,
        }

    @staticmethod
    def _call_object_rightclick_callback_if_exists(obj: Union[Axes, Artist], mouse_event) -> bool:
        on_rightclick = getattr(obj, '_quibbler_on_rightclick', None)
        has_rightclick_callback = on_rightclick is not None
        if has_rightclick_callback:
            on_rightclick(mouse_event)

        return has_rightclick_callback

    def _handle_button_press(self, mouse_event: MouseEvent):
        start_dragging(id(self), False)
        if mouse_event.button is MouseButton.RIGHT:
            self._call_object_rightclick_callback_if_exists(mouse_event.inaxes, mouse_event)

    def _handle_button_release(self, _mouse_event: MouseEvent):
        end_dragging(id(self))
        self.enhanced_pick_event = None

    def _handle_pick_event(self, pick_event: PickEvent):
        start_dragging(id(self))
        self.enhanced_pick_event = EnhancedPickEventWithFuncArgsKwargs.from_pick_event(pick_event)
        if self.enhanced_pick_event.button is MouseButton.RIGHT:
            if not self._call_object_rightclick_callback_if_exists(pick_event.artist, pick_event.mouseevent):
                self._inverse_from_mouse_event(pick_event.mouseevent)

    def _inverse_assign_graphics(self, mouse_event: MouseEvent):
        """
        Reverse any relevant quibs in artists creation args
        """
        # We record the current pick_event to avoid a race condition when calling inverse_assign_drawing_func
        enhanced_pick_event = self.enhanced_pick_event
        if enhanced_pick_event is None:
            # This case was observed in the wild
            return

        with timeit("motion_notify", "motion notify"), graphics_assignment_mode(mouse_event.inaxes):
            graphics_inverse_assigner.inverse_assign_drawing_func(
                mouse_event=mouse_event,
                enhanced_pick_event=enhanced_pick_event)

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
        if self.enhanced_pick_event is not None:
            with self._try_acquire_assignment_lock() as locked:
                if locked:
                    # If not locked, there is already another motion handler running, we just drop this one.
                    # This could happen if changes are slow or if a dialog is open
                    self._inverse_assign_graphics(mouse_event)
                    if END_DRAG_IMMEDIATELY:
                        self.enhanced_pick_event = None

    def initialize(self):
        """
        Initializes the canvas events handler to receive events from the canvas
        """
        self._handler_ids = []
        for event_type, handler in self.EVENT_HANDLERS.items():
            self._handler_ids.append(self.canvas.mpl_connect(event_type, handler))

        self._original_destroy = self.canvas.manager.destroy

        self.canvas.manager.destroy = self._manager_destroy

    def _manager_destroy(self):
        self._original_destroy()
        self.disconnect()

    def _delete_all_graphics_quibs(self):
        if isinstance(self.canvas, FigureCanvasBase):
            for artist in _get_all_artists_from_axes_of_figure(self.canvas.figure):
                clear_all_quibs(artist)

    def disconnect(self, _event=None):
        for handler_id in self._handler_ids:
            self.canvas.mpl_disconnect(handler_id)
        self.CANVASES_TO_TRACKERS.pop(self.canvas, None)
        self.canvas.manager.destroy = self._original_destroy
        self._original_destroy = None
        self._delete_all_graphics_quibs()
        self.CANVASES_TO_TRACKERS.pop(self.canvas, None)

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
