from __future__ import annotations
from typing import List, Type, TYPE_CHECKING
from typing import Any, List, Type, TYPE_CHECKING, Tuple

from .exceptions import CannotReverseUnknownFunctionException
from .elementwise_reverser import ElementWiseReverser
from .transpositional_reverser import TranspositionalReverser
from .. import Assignment
from ..assignment import QuibWithAssignment

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib
    from pyquibbler.quib.assignment.reverse_assignment.reverser import Reverser

REVERSER_CLASSES: List[Type[Reverser]] = [TranspositionalReverser, ElementWiseReverser]
REVERSER_CLS_BY_FUNC = {func: reverser_cls
                        for reverser_cls in REVERSER_CLASSES
                        for func in reverser_cls.SUPPORTED_FUNCTIONS}


def _run_reverser_on_function_quib_and_assignment(reverser_cls: Type[Reverser],
                                                 function_quib: FunctionQuib,
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

    quibs_with_assignments = reverser_cls(function_quib=function_quib,
                                          assignment=Assignment(
                                              paths=[current_path],
                                              value=assignment.value)).get_quibs_with_assignments()

    for quib_with_assignment in quibs_with_assignments:
        quib_with_assignment.assignment.paths.extend(paths_at_end)
        quib_with_assignment.apply()


def reverse_function_quib(function_quib: FunctionQuib, assignment: Assignment) -> List[QuibWithAssignment]:
    """
    Given a function quib and a change in it's result (at `indices` to `value`), reverse assign relevant values
    to relevant quib arguments
    """
    reverser_cls = REVERSER_CLS_BY_FUNC.get(function_quib.func)
    if reverser_cls is None:
        raise CannotReverseUnknownFunctionException(function_quib.func)
    return reverser_cls(function_quib=function_quib, assignment=assignment).get_reversed_quibs_with_assignments()


def get_override_options(quib_with_assignment: QuibWithAssignment) -> Tuple[List[QuibWithAssignment], List]:
    from pyquibbler.quib import FunctionQuib
    options = []
    reversals = [quib_with_assignment]
    while len(reversals) == 1:
        reversal = reversals[0]
        if reversal.quib.allow_overriding:
            options.append(reversal)
        if isinstance(reversal.quib, FunctionQuib):
            try:
                reversals = reverse_function_quib(reversal.quib, reversal.assignment)
            except CannotReverseUnknownFunctionException:
                reversals = []
        else:
            reversals = []
    diverged_options = [get_override_options(reversal) for reversal in reversals]
    if not all(option[0] or option[1] for option in diverged_options):
        # If one of the diverged options does not allow overriding, then we can't reverse assign through the diverger -
        # only one of the reverse assignment threads will be able to end with an override.
        diverged_options = []
    return options, diverged_options
