from __future__ import annotations
from collections import defaultdict
from typing import List, Iterable, Mapping, TYPE_CHECKING

from pyquibbler.quib.assignment import QuibWithAssignment
from pyquibbler.quib.function_quibs import CannotAssignException

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


def filter_quibs_with_assignment_with_ancestor_in_different_quibs_with_assignments(
        quibs_with_assignments: Iterable[QuibWithAssignment]):
    """
    Filter out assignments to quibs for which there is an assigment to an ancestor of
    """
    assigned_quibs = set(quib_with_assignment.quib for quib_with_assignment in quibs_with_assignments)
    return [
        quib_with_assignment
        for quib_with_assignment in quibs_with_assignments
        if not quib_with_assignment.quib.ancestors.intersection(assigned_quibs)
    ]


def get_ancestors_to_assignments(quibs_with_assignments: Iterable[QuibWithAssignment]
                                 ) -> Mapping[Quib, List[QuibWithAssignment]]:
    ancestors_to_assignments = defaultdict(list)
    for quib_with_assignment in quibs_with_assignments:
        for ancestor in quib_with_assignment.quib.ancestors:
            ancestors_to_assignments[ancestor].append(quib_with_assignment)
    return ancestors_to_assignments


def apply_assignment_group(quibs_with_assignments: List[QuibWithAssignment]):
    """
    Applies a group of assignments.
    When we logically want to apply a group of assignments and not individual assignments,
    there are two corner cases we have to take care of:
    1. One assignment is done to a quib, which is the ancestor of another quib which there is an assignment to
       In this case we assign only to the upstream quib.
    2. Multiple assignments are done to quibs with a common ancestor.
       In this case we want to perform only one of them, so we try them one by one until one succeeds.
    """
    quibs_with_assignments = \
        filter_quibs_with_assignment_with_ancestor_in_different_quibs_with_assignments(quibs_with_assignments)
    ancestors_to_assignments = get_ancestors_to_assignments(quibs_with_assignments)
    blacklist = set()
    for quib_with_assignment in quibs_with_assignments:
        if quib_with_assignment not in blacklist:
            try:
                quib_with_assignment.apply()
            except CannotAssignException:
                pass
            else:
                for ancestor in quib_with_assignment.quib.ancestors:
                    blacklist.update(ancestors_to_assignments[ancestor])
