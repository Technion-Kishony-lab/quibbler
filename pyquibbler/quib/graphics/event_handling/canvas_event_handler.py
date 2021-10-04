from typing import Optional, TYPE_CHECKING, Sized, List, Tuple, Any

from matplotlib.backend_bases import MouseEvent, PickEvent

from pyquibbler.performance_utils import timer
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
from pyquibbler.quib.graphics.event_handling import graphics_reverse_assigner

if TYPE_CHECKING:
    from pyquibbler.quib.graphics.graphics_function_quib import GraphicsFunctionQuib


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

        self.EVENT_HANDLERS = {
            'button_release_event': self._handle_button_release,
            'motion_notify_event': self._handle_motion_notify,
            'pick_event': self._handle_pick_event
        }

    def _handle_button_release(self, mouse_event: MouseEvent):
        self.current_pick_event = None

    def _handle_pick_event(self, pick_event: PickEvent):
        self.current_pick_event = pick_event

    def _reverse_assign_graphics_function_quibs(self, mouse_event: MouseEvent,
                                                graphics_function_quibs: List['GraphicsFunctionQuib']):
        """
        Reverse each of the graphics function quibs (each by finding a corresponding reverse assigner)
        given the mouse event
        """
        with timer(name="motion_notify"), aggregate_redraw_mode():
            for graphics_function_quib in graphics_function_quibs:
                graphics_reverse_assigner.reverse_graphics_function_quib(graphics_function_quib=graphics_function_quib,
                                                                         mouse_event=mouse_event,
                                                                         pick_event=self.current_pick_event)

    def _handle_motion_notify(self, mouse_event: MouseEvent):
        if self.current_pick_event is not None:
            graphics_function_quibs = getattr(self.current_pick_event.artist, 'graphics_function_quibs')
            if graphics_function_quibs is not None:
                self._reverse_assign_graphics_function_quibs(mouse_event, graphics_function_quibs)

    def initialize(self):
        """
        Initializes the canvas events handler to receive events from the canvas
        """
        for event_type, handler in self.EVENT_HANDLERS.items():
            self.canvas.mpl_connect(event_type, handler)
