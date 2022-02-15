from typing import Any, List, Tuple
from matplotlib.pyplot import Axes

from pyquibbler.assignment.override_choice import get_overrides_for_quib_change_group
from pyquibbler.path import PathComponent
from pyquibbler.assignment import AssignmentToQuib, Assignment
from pyquibbler.assignment import OverrideRemoval, OverrideGroup


def get_override_group_for_axes_set_lim(args: List[Any], lim: Tuple[float, float], is_override_removal: bool) \
        -> OverrideGroup:
    from pyquibbler.quib import Quib
    assert len(args) > 1
    assert isinstance(args[0], Axes)
    if len(args) == 2 and isinstance(args[1], Quib):

        # set_xlim(ax, quib)
        quib = args[1]
        changes = [AssignmentToQuib(quib, Assignment(
            value=lim,
            path=[PathComponent(quib.get_type(), slice(0, 2))]))]
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
                AssignmentToQuib(min_, Assignment(
                    value=lim[0],
                    path=[]))
            )
        if isinstance(max_, Quib):
            changes.append(
                AssignmentToQuib(max_, Assignment(
                    value=lim[1],
                    path=[]))
            )

    return get_overrides_for_quib_change_group(changes)
