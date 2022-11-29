from typing import Tuple

from matplotlib.pyplot import Axes

from pyquibbler.utilities.general_utils import Args

from pyquibbler.assignment import create_assignment, AssignmentToQuib, OverrideGroup, \
    get_override_group_for_quib_changes
from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
from pyquibbler.path import PathComponent


# TODO: might be helpful to implement is_override_removal=True which will be called for example upon
#  right click the axis


def get_override_group_for_axes_set_lim(args: Args, lim: Tuple[float, float], is_override_removal: bool) \
        -> OverrideGroup:
    from pyquibbler.quib.quib import Quib
    assert len(args) > 1
    assert isinstance(args[0], Axes)

    tolerance = None if GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val is None \
        else (lim[1] - lim[0]) / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val

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
