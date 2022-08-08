from typing import Callable, List, Any, Iterable, Tuple
from matplotlib.backend_bases import MouseEvent, PickEvent

from pyquibbler.assignment import AssignmentToQuib
from pyquibbler.assignment import AssignmentCancelledByUserException
from pyquibbler.quib.graphics.event_handling.set_lim_inverse_assigner import get_override_group_for_axes_set_lim

GRAPHICS_REVERSE_ASSIGNERS = {}


def graphics_inverse_assigner(graphics_func_names_to_handle: List[str]):
    """
    Decorate a function capable of inverse assigning to argument quibs given a mouse event
    """

    def _decorator(func: Callable[[PickEvent, MouseEvent, List[Any]], List[AssignmentToQuib]]):
        for func_name in graphics_func_names_to_handle:
            GRAPHICS_REVERSE_ASSIGNERS[func_name] = func
        return func

    return _decorator


def inverse_assign_drawing_func(drawing_func: Callable,
                                args: Iterable[Any],
                                pick_event: PickEvent,
                                mouse_event: MouseEvent):
    """
    Reverse a graphics function quib, assigning to all it's arguments values based on pick event and mouse event
    """
    assert pick_event is not None
    inverse_assigner_func = GRAPHICS_REVERSE_ASSIGNERS.get(drawing_func.__qualname__)
    if inverse_assigner_func is not None:
        try:
            override_group = inverse_assigner_func(pick_event=pick_event, mouse_event=mouse_event, args=args)
        except AssignmentCancelledByUserException:
            pass
        else:
            override_group.apply(on_drag=True)
            return override_group


def inverse_assign_axes_lim_func(args: Iterable[Any],
                                 lim: Tuple[float, float],
                                 is_override_removal: bool,
                                 ):
    """
    Reverse a graphics set axis lim quib, assigning to it's argument values based on change in axes
    """

    try:
        override_group = get_override_group_for_axes_set_lim(
            args=args,
            lim=lim,
            is_override_removal=is_override_removal,
        )
    except AssignmentCancelledByUserException:
        pass
    else:
        override_group.apply(on_drag=True)
        return override_group
