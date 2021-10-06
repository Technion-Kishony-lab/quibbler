from __future__ import annotations
from typing import Any, Iterable, TYPE_CHECKING, List, Set

from pyquibbler.quib.assignment.assignment import QuibWithAssignment

from pyquibbler.quib.assignment import Assignment

if TYPE_CHECKING:
    from pyquibbler.quib import Quib, FunctionQuib


def _quib_with_ancestors(quib: Quib) -> Set[Quib]:
    """
    Get the ancestors of a quib (if relevant) together with it
    """
    from pyquibbler.quib import FunctionQuib
    if not isinstance(quib, FunctionQuib):
        return {quib}
    return {quib, *quib.ancestors}


def quib_has_ancestor_in_other_quibs(quib: Quib, quibs: List[Quib]):
    """
    Whether or not a quib has an ancestor in a group of other quibs
    """
    from pyquibbler.quib import FunctionQuib
    if not isinstance(quib, FunctionQuib):
        return False

    return any(quib in {_quib_with_ancestors(other_quib)}
               for other_quib in quibs)


def quib_with_assignment_has_ancestor_in_different_quibs_with_assignments(
        quib_with_assignment: QuibWithAssignment, quibs_with_assignments: Iterable[QuibWithAssignment]):
    """
    Whether or not a quib_with_assignment has an ancestor in other quibs_with_assignments
    """
    other_quibs = [quib_with_assignment.quib
                   for quib_with_assignment in quibs_with_assignments
                   if quib_with_assignment.quib is not quib_with_assignment.quib]

    return quib_has_ancestor_in_other_quibs(quib_with_assignment.quib, other_quibs)


def filter_quibs_with_assignments_with_common_ancestors(quibs_with_assignments: Iterable[QuibWithAssignment]):
    """
    Filter out quibs_with_assignments so that there won't be two quibs_with_assignments quibs' with the same ancestor
    (one will be chosen at random)
    """
    filtered = []
    filtered_ancestors = set()
    for quib_with_assignment in quibs_with_assignments:
        if not (_quib_with_ancestors(quib_with_assignment.quib) & filtered_ancestors):
            filtered.append(quib_with_assignment)
            filtered_ancestors |= _quib_with_ancestors(quib_with_assignment.quib)
    return filtered


def filter_quibs_with_assignments(quibs_with_assignments: List[QuibWithAssignment]):
    """
    Filter `quibs_with_assignments` so that there won't be quibs that:
    1.Have a common ancestor in other quibs with assignments
    2 Both attempt to change the same common ancestor (one will be choosed at random)
    """
    filtered_quibs_with_assignments = [
        quib_with_assignment
        for quib_with_assignment in quibs_with_assignments
        if not quib_with_assignment_has_ancestor_in_different_quibs_with_assignments(quib_with_assignment,
                                                                                     quibs_with_assignments)
    ]

    filtered_quibs_with_assignments = filter_quibs_with_assignments_with_common_ancestors(
        filtered_quibs_with_assignments
    )

    return filtered_quibs_with_assignments
