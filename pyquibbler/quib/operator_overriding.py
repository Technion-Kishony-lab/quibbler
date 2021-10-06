"""
Override Quib operators by replacing magic methods with function quib wrappers that wrap operator function
from the operator module.
We have to use the operator functions in order to allow builtin operator functionality:
1. Calling reverse arithmetic operations when the normal ones return NotImplemented
2. Cases where a magic method is not present on a built-in type but the operator works anyway (e.g. float.__ceil__).
"""
import operator
from math import trunc, floor, ceil
from typing import Callable, Tuple

from .function_quibs import DefaultFunctionQuib
from .quib import Quib


def operator_override(operator_name: str) -> Tuple[str, Callable]:
    return operator_name, getattr(operator, operator_name)


def reverse_operator_override(operator_name: str) -> Tuple[str, Callable]:
    non_reverse_operator = getattr(operator, '__' + operator_name[3:])
    return operator_name, lambda self, other: non_reverse_operator(other, self)


ARITHMETIC_OVERRIDES = [
    operator_override('__add__'),
    operator_override('__sub__'),
    operator_override('__mul__'),
    operator_override('__matmul__'),
    operator_override('__truediv__'),
    operator_override('__floordiv__'),
    operator_override('__mod__'),
    ('__divmod__', divmod),
    operator_override('__pow__'),
    operator_override('__lshift__'),
    operator_override('__rshift__'),
    operator_override('__and__'),
    operator_override('__xor__'),
    operator_override('__or__'),
]

REVERSE_ARITHMETIC_OVERRIDES = [
    reverse_operator_override('__radd__'),
    reverse_operator_override('__rsub__'),
    reverse_operator_override('__rmul__'),
    reverse_operator_override('__rmatmul__'),
    reverse_operator_override('__rtruediv__'),
    reverse_operator_override('__rfloordiv__'),
    reverse_operator_override('__rmod__'),
    ('__rdivmod__', lambda self, other: divmod(other, self)),
    reverse_operator_override('__rpow__'),
    reverse_operator_override('__rlshift__'),
    reverse_operator_override('__rrshift__'),
    reverse_operator_override('__rand__'),
    reverse_operator_override('__rxor__'),
    reverse_operator_override('__ror__'),
]

UNARY_OVERRIDES = [
    operator_override('__neg__'),
    operator_override('__pos__'),
    operator_override('__abs__'),
    operator_override('__invert__'),
]

COMPARISON_OVERRIDES = [
    operator_override('__lt__'),
    operator_override('__gt__'),
    operator_override('__ge__'),
    operator_override('__le__'),
]

ROUNDING_OVERRIDES = [
    ('__round__', round),
    ('__trunc__', trunc),
    ('__floor__', floor),
    ('__ceil__', ceil),
]


ALL_OVERRIDES = ARITHMETIC_OVERRIDES + REVERSE_ARITHMETIC_OVERRIDES + UNARY_OVERRIDES + ROUNDING_OVERRIDES + \
                COMPARISON_OVERRIDES


def override_quib_operators():
    """
    Make operators (and other magic methods) on quibs return quibs.
    Overriding __getattr__ does not suffice because lookup of magic methods does not go
    through the standard getattr process.
    See more here: https://docs.python.org/3/reference/datamodel.html#special-method-lookup
    """
    for name, wrapped in ALL_OVERRIDES:
        assert name not in vars(Quib), name
        setattr(Quib, name, DefaultFunctionQuib.create_wrapper(wrapped))
