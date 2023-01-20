from dataclasses import dataclass

from matplotlib.backend_bases import MouseEvent, PickEvent, MouseButton
from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.quib.graphics import artist_wrapper
from pyquibbler.quib.graphics.event_handling.enhance_pick_event import enhance_pick_event


@dataclass
class PickHandler:
    pick_event: PickEvent
    func_args_kwargs: FuncArgsKwargs


def create_pick_handler(pick_event: PickEvent):
    enhance_pick_event(pick_event)
    return PickHandler(
        pick_event=pick_event,
        func_args_kwargs=artist_wrapper.get_creating_quib(pick_event.artist).handler.func_args_kwargs,
    )
