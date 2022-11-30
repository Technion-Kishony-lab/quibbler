from typing import Callable, List, Any, Tuple
from matplotlib.backend_bases import MouseEvent, PickEvent, MouseButton

from pyquibbler.assignment import AssignmentToQuib, OverrideGroup
from pyquibbler.assignment import AssignmentCancelledByUserException
from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.quib.graphics.event_handling.set_lim_inverse_assigner import get_override_group_for_axes_set_lim
from pyquibbler.utilities.general_utils import Args

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


def inverse_assign_drawing_func(func_args_kwargs: FuncArgsKwargs,
                                pick_event: PickEvent,
                                mouse_event: MouseEvent,
                                ):
    """
    Reverse a graphics function quib, assigning to all it's arguments values based on pick event and mouse event
    """
    assert pick_event is not None
    drawing_func = func_args_kwargs.func
    inverse_assigner_func = GRAPHICS_REVERSE_ASSIGNERS.get(drawing_func.__qualname__)
    if inverse_assigner_func is not None:
        try:
            override_group: OverrideGroup = inverse_assigner_func(pick_event=pick_event,
                                                                  mouse_event=mouse_event,
                                                                  func_args_kwargs=func_args_kwargs,
                                                                  )
        except AssignmentCancelledByUserException:
            pass
        else:
            override_group.apply(is_dragging=pick_event.mouseevent.button is not MouseButton.RIGHT)
            return override_group


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
        override_group.apply(is_dragging=True)
        return override_group
