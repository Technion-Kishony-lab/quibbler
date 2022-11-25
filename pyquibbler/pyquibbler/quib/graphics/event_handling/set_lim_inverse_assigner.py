from typing import Any, List, Tuple, Callable

from matplotlib.pyplot import Axes

from pyquibbler.assignment import create_assignment, AssignmentToQuib, OverrideGroup, \
    get_override_group_for_quib_changes, get_axes_x_y_tolerance
from pyquibbler.path import PathComponent


# TODO: might be helpful to implement is_override_removal=True which will be called for example upon
#  right click the axis

def get_override_group_for_axes_set_lim(func_name: str, args: List[Any], lim: Tuple[float, float], is_override_removal: bool) \
        -> OverrideGroup:
    from pyquibbler.quib.quib import Quib
    assert len(args) > 1
    ax = args[0]
    assert isinstance(ax, Axes)

    # get assignment tolerance:
    tolerance_x, tolerance_y = get_axes_x_y_tolerance(ax)
    tolerance = tolerance_x if func_name == 'set_xlim' else tolerance_y

    # get changes:
    if len(args) == 2 and isinstance(args[1], Quib):

        # set_xlim(ax, quib)
        quib = args[1]
        changes = [AssignmentToQuib(quib, create_assignment(
            value=lim,
            path=[PathComponent(slice(0, 2))],
            tolerance=tolerance
        ))]
    else:
        if len(args) == 2:
            assert len(args[1]) == 2

            # set_xlim(ax, [min, max])
            min_ = args[1][0]
            max_ = args[1][1]
        elif len(args) == 3:

            # set_xlim(ax, min, max)
            min_ = args[1]
            max_ = args[2]
        else:
            assert False

        changes = []
        if isinstance(min_, Quib):
            changes.append(
                AssignmentToQuib(min_, create_assignment(
                    value=lim[0],
                    path=[],
                    tolerance=tolerance
                ))
            )
        if isinstance(max_, Quib):
            changes.append(
                AssignmentToQuib(max_, create_assignment(
                    value=lim[1],
                    path=[],
                    tolerance=tolerance
                ))
            )

    return get_override_group_for_quib_changes(changes)
