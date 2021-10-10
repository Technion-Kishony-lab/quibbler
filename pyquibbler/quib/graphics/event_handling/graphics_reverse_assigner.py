from typing import Callable, TYPE_CHECKING, List, Any, Iterable
from matplotlib.backend_bases import MouseEvent, PickEvent

from pyquibbler.quib.assignment.assignment import QuibWithAssignment

if TYPE_CHECKING:
    from pyquibbler.quib.graphics import GraphicsFunctionQuib

GRAPHICS_REVERSE_ASSIGNERS = {}


def graphics_reverse_assigner(graphics_func_name_to_handle: str):
    """
    Decorate a function capable of reverse assigning to argument quibs given a mouse event
    """

    def _decorator(func: Callable[[PickEvent, MouseEvent, 'GraphicsFunctionQuib'], List[QuibWithAssignment]]):
        GRAPHICS_REVERSE_ASSIGNERS[graphics_func_name_to_handle] = func
        return func

    return _decorator


def reverse_assign_drawing_func(drawing_func: Callable,
                                args: Iterable[Any],
                                pick_event: PickEvent,
                                mouse_event: MouseEvent):
    """
    Reverse a graphics function quib, assigning to all it's arguments values based on pick event and mouse event
    """
    reverse_assigner_func = GRAPHICS_REVERSE_ASSIGNERS.get(drawing_func.__qualname__)
    if reverse_assigner_func is not None:
        quibs_with_assignments = reverse_assigner_func(pick_event=pick_event, mouse_event=mouse_event, args=args)
        from pyquibbler.quib import Quib
        Quib.apply_assignment_group(quibs_with_assignments)
