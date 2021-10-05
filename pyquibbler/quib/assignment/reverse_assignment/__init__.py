from __future__ import annotations
from typing import List, Type, TYPE_CHECKING

from .exceptions import CannotReverseUnknownFunctionException
from .elementwise_reverser import ElementWiseReverser
from .transpositional_reverser import TranspositionalReverser
from .. import Assignment

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


def reverse_function_quib(function_quib: FunctionQuib,
                          assignment: Assignment) -> None:
    """
    Given a function quib and a change in it's result (at `indices` to `value`), reverse assign relevant values
    to relevant quib arguments
    """
    reverser_cls = REVERSER_CLS_BY_FUNC.get(function_quib.func)
    if reverser_cls is None:
        raise CannotReverseUnknownFunctionException(function_quib.func)
    return reverser_cls(function_quib=function_quib, assignment=assignment).reverse()
