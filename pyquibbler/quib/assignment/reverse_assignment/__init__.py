from __future__ import annotations
from typing import List, Type, TYPE_CHECKING

from .exceptions import CannotReverseUnknownFunctionException, CannotReverseException
from .elementwise_reverser import ElementWiseReverser
from .transpositional_reverser import TranspositionalReverser
from ..assignment import Assignment, QuibWithAssignment

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib
    from pyquibbler.quib.assignment.reverse_assignment.reverser import Reverser

REVERSER_CLASSES: List[Type[Reverser]] = [TranspositionalReverser, ElementWiseReverser]
reverser_cls_by_func = {}
for reverser_cls in REVERSER_CLASSES:
    for func in reverser_cls.SUPPORTED_FUNCTIONS:
        assert reverser_cls_by_func.setdefault(func, reverser_cls) is reverser_cls


def _get_reversed_quibs_with_assignments_from_reverser(reverser_cls: Type[Reverser], function_quib: FunctionQuib,
                                                       assignment: Assignment):
    """
    Runs a reverser, wrapping up all logic with paths (such as dealing with field arrays)
    """
    paths_at_end = assignment.paths[1:]
    current_path = assignment.paths[0]

    # If we're setting a field, we want to emulate the function having replaced the entire object instead of just the
    # referenced field (so we can do any index + quib choosing games);
    # then when we add in the field in the path after it the overrider will create the desired affect
    # of only changing the referenced field
    if isinstance(assignment.paths[0], str):
        paths_at_end = [assignment.paths[0], *paths_at_end]
        current_path = ...

    reverser = reverser_cls(function_quib, Assignment(assignment.value, [current_path]))
    quibs_with_assignments = reverser.get_reversed_quibs_with_assignments()

    for quib_with_assignment in quibs_with_assignments:
        quib_with_assignment.assignment.paths.extend(paths_at_end)

    return quibs_with_assignments


def get_reversals_for_assignment(function_quib: FunctionQuib, assignment: Assignment) -> List[QuibWithAssignment]:
    """
    Given a function quib and a change in it's result (at `indices` to `value`), reverse assign relevant values
    to relevant quib arguments
    """
    reverser_cls = reverser_cls_by_func.get(function_quib.func)
    if reverser_cls is None:
        raise CannotReverseUnknownFunctionException(function_quib, assignment)
    return _get_reversed_quibs_with_assignments_from_reverser(reverser_cls, function_quib=function_quib,
                                                              assignment=assignment)
