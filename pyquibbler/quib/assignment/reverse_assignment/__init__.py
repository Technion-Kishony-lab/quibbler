from __future__ import annotations
from typing import Any, List, Type, TYPE_CHECKING

from .exceptions import CannotReverseUnknownFunctionException
from .elementwise_reverser import ElementWiseReverser
from .transpositional_reverser import TranspositionalReverser
from .. import Assignment

if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib
    from pyquibbler.quib.assignment.reverse_assignment.reverser import Reverser

REVERSERS: List[Type[Reverser]] = [TranspositionalReverser, ElementWiseReverser]


def reverse_function_quib(function_quib: FunctionQuib,
                          assignment: Assignment) -> None:
    """
    Given a function quib and a change in it's result (at `indices` to `value`), reverse assign relevant values
    to relevant quib arguments
    """
    for reverser_cls in REVERSERS:
        if reverser_cls.matches(function_quib):
            reverser_cls(function_quib=function_quib, assignment=assignment).reverse()
            return
    raise CannotReverseUnknownFunctionException(function_quib.func)
