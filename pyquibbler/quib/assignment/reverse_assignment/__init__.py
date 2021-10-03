from typing import Any, List, Type
from .exceptions import CannotReverseUnknownFunctionException

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib import FunctionQuib
    from pyquibbler.quib.assignment.reverse_assignment.reverser import Reverser


def reverse_function_quib(function_quib: 'FunctionQuib',
                          indices: Any,
                          value: Any) -> None:
    """
    Given a function quib and a change in it's result (at `indices` to `value`), reverse assign relevant values
    to relevant quib arguments
    """
    from .elementwise_reverser import ElementWiseReverser
    from .transpositional_reverser import TranspositionalReverser

    reversers: List[Type[Reverser]] = [TranspositionalReverser, ElementWiseReverser]

    for reverser_cls in reversers:
        if reverser_cls.matches(function_quib):
            reverser_cls(function_quib=function_quib, indices=indices, value=value).reverse()
            return
    raise CannotReverseUnknownFunctionException(function_quib.func)
