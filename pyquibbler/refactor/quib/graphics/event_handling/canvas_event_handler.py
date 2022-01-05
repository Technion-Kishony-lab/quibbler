from contextlib import contextmanager
from threading import Lock
from typing import Optional
from matplotlib.artist import Artist
from matplotlib.backend_bases import MouseEvent, PickEvent, MouseButton

from pyquibbler.refactor.env import END_DRAG_IMMEDIATELY
from pyquibbler.refactor.logger import logger
from pyquibbler.refactor.performance_utils import timer
from pyquibbler.refactor.quib.graphics.redraw import aggregate_redraw_mode
from pyquibbler.refactor.quib.graphics.event_handling import graphics_inverse_assigner


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
        self._last_mouse_event_with_overrides: Optional[PickEvent] = None
        self._assignment_lock = Lock()

        self.EVENT_HANDLERS = {
            'button_release_event': self._handle_button_release,
            'motion_notify_event': self._handle_motion_notify,
            'pick_event': self._handle_pick_event
        }

    def _handle_button_release(self, _mouse_event: MouseEvent):
        if self._last_mouse_event_with_overrides:
            from pyquibbler.refactor.quib.graphics import releasing
            with releasing():
                self._inverse_from_mouse_event(mouse_event=self._last_mouse_event_with_overrides)
        self._last_mouse_event_with_overrides = None
        self.current_pick_event = None

    def _handle_pick_event(self, pick_event: PickEvent):
        self.current_pick_event = pick_event
        if pick_event.mouseevent.button is MouseButton.RIGHT:
            self._inverse_from_mouse_event(pick_event.mouseevent)

    def _inverse_assign_graphics(self, artist: Artist, mouse_event: MouseEvent):
        """
        Reverse any relevant quibs in artists creation args
        """
        # We record the current pick_event to avoid a race condition when calling inverse_assign_drawing_func
        pick_event = self.current_pick_event
        if pick_event is None:
            # This case was observed in the wild
            return
        drawing_func = getattr(artist, '_quibbler_drawing_func')
        args = getattr(artist, '_quibbler_args')
        with timer("motion_notify", lambda x: logger.info(f"motion notify {x}")), aggregate_redraw_mode():
            override_group = graphics_inverse_assigner.inverse_assign_drawing_func(drawing_func=drawing_func,
                                                                                   args=args,
                                                                                   mouse_event=mouse_event,
                                                                                   pick_event=pick_event)
            if override_group is not None and override_group:
                self._last_mouse_event_with_overrides = mouse_event

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
        from pyquibbler.refactor.quib.graphics import dragging
        with dragging():
            self._inverse_from_mouse_event(mouse_event)

    def _inverse_from_mouse_event(self, mouse_event):
        if self.current_pick_event is not None:
            drawing_func = getattr(self.current_pick_event.artist, '_quibbler_drawing_func', None)
            if drawing_func is not None:
                with self._try_acquire_assignment_lock() as locked:
                    if locked:
                        # If not locked, there is already another motion handler running, we just drop this one.
                        # This could happen if changes are slow or if a dialog is open
                        self._inverse_assign_graphics(self.current_pick_event.artist, mouse_event)
                        if END_DRAG_IMMEDIATELY:
                            self.current_pick_event = None

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

        handler_ids.append(self.canvas.mpl_connect('close_event', disconnect))