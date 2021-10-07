from contextlib import contextmanager
from threading import Lock
from typing import Optional
from matplotlib.artist import Artist
from matplotlib.backend_bases import MouseEvent, PickEvent

from pyquibbler.performance_utils import timer
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
from pyquibbler.quib.graphics.event_handling import graphics_reverse_assigner


class CanvasEventHandler:
    """
    Handles all events from the canvas (such as press, drag, and pick), reverse assigning to the relevant quibs
    using a specific graphics reverse assignment function handler
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
        self.previous_mouse_event: Optional[PickEvent] = None
        self._assignment_lock = Lock()

        self.EVENT_HANDLERS = {
            'button_release_event': self._handle_button_release,
            'motion_notify_event': self._handle_motion_notify,
            'pick_event': self._handle_pick_event
        }

    def _handle_button_release(self, _mouse_event: MouseEvent):
        self.current_pick_event = None

    def _handle_pick_event(self, pick_event: PickEvent):
        self.current_pick_event = pick_event

    def _reverse_assign_graphics(self, artist: Artist, mouse_event: MouseEvent):
        """
        Reverse any relevant quibs in artists creation args
        """
        drawing_func = getattr(artist, '_quibbler_drawing_func', None)
        args = getattr(artist, '_quibbler_args', tuple())
        with timer(name="motion_notify"), aggregate_redraw_mode():
            graphics_reverse_assigner.reverse_assign_drawing_func(drawing_func=drawing_func,
                                                                     args=args,
                                                                     mouse_event=mouse_event,
                                                                     pick_event=self.current_pick_event)

    @contextmanager
    def _try_acquire_assignment_lock(self):
        locked = self._assignment_lock.acquire(blocking=False)
        try:
            yield locked
        finally:
            if locked:
                self._assignment_lock.release()

    def _handle_motion_notify(self, mouse_event: MouseEvent):
        if self.current_pick_event is not None:
            drawing_func = getattr(self.current_pick_event.artist, '_quibbler_drawing_func', None)
            if drawing_func is not None:
                with self._try_acquire_assignment_lock() as locked:
                    if locked:
                        # If not locked, there is already another motion handler running, we just drop this one.
                        # This could happen if changes are slow or if a dialog is open
                        self._reverse_assign_graphics(self.current_pick_event.artist, mouse_event)

    def initialize(self):
        """
        Initializes the canvas events handler to receive events from the canvas
        """
        for event_type, handler in self.EVENT_HANDLERS.items():
            self.canvas.mpl_connect(event_type, handler)
