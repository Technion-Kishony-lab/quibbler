from typing import Callable, List, Any, Tuple
from matplotlib.backend_bases import MouseEvent, PickEvent

from pyquibbler.assignment import AssignmentToQuib, OverrideGroup
from pyquibbler.assignment import AssignmentCancelledByUserException
from pyquibbler.utilities.general_utils import Args
from .enhance_pick_event import EnhancedPickEventWithFuncArgsKwargs

from .set_lim_inverse_assigner import get_override_group_for_axes_set_lim

GRAPHICS_REVERSE_ASSIGNERS: dict[str, Callable[[EnhancedPickEventWithFuncArgsKwargs, MouseEvent], OverrideGroup]] = {}


def graphics_inverse_assigner(graphics_func_names_to_handle: List[str]):
    """
    Decorate a function capable of inverse assigning to argument quibs given a mouse event
    """

    def _decorator(func: Callable[[PickEvent, MouseEvent, List[Any]], List[AssignmentToQuib]]):
        for func_name in graphics_func_names_to_handle:
            GRAPHICS_REVERSE_ASSIGNERS[func_name] = func
        return func

    return _decorator


def inverse_assign_drawing_func(enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs,
                                mouse_event: MouseEvent,
                                ):
    """
    Reverse a graphics function quib, assigning to all it's arguments values based on pick event and mouse event
    """
    assert enhanced_pick_event is not None
    func_args_kwargs = enhanced_pick_event.func_args_kwargs
    drawing_func = func_args_kwargs.func
    inverse_assigner_func = GRAPHICS_REVERSE_ASSIGNERS.get(drawing_func.__qualname__)
    if inverse_assigner_func is None:
        return

    try:
        override_group = inverse_assigner_func(enhanced_pick_event, mouse_event)
    except AssignmentCancelledByUserException:
        pass
    else:
        override_group.apply()


def inverse_assign_axes_lim_func(args: Args,
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
        override_group.apply()
