"""
Override Quib operators by replacing magic methods with function quib wrappers that wrap operator function
from the operator module.
We have to use the operator functions in order to allow builtin operator functionality:
1. Calling reverse arithmetic operations when the normal ones return NotImplemented
2. Cases where a magic method is not present on a built-in type but the operator works anyway (e.g. float.__ceil__).
"""
import functools
import operator
from functools import wraps
from math import trunc, floor, ceil
from typing import Callable, Tuple, Optional, Type

from .function_quibs import DefaultFunctionQuib
from .function_quibs.elementwise_quib import ElementWiseQuib
from .quib import Quib


def operator_override(operator_name: str, cls: Type[DefaultFunctionQuib] = None) -> Tuple[Type[DefaultFunctionQuib],
                                                                                          str, Callable]:
    cls = cls or DefaultFunctionQuib
    return cls, operator_name, getattr(operator, operator_name)


ARITHMETIC_OVERRIDES = [
    operator_override('__add__', ElementWiseQuib),
    operator_override('__sub__', ElementWiseQuib),
    operator_override('__mul__', ElementWiseQuib),
    operator_override('__matmul__'),
    operator_override('__truediv__', ElementWiseQuib),
    operator_override('__floordiv__'),
    operator_override('__mod__', ElementWiseQuib),
    (DefaultFunctionQuib, '__divmod__', divmod),
    operator_override('__pow__', ElementWiseQuib),
    operator_override('__lshift__'),
    operator_override('__rshift__'),
    operator_override('__and__', ElementWiseQuib),
    operator_override('__xor__', ElementWiseQuib),
    operator_override('__or__', ElementWiseQuib),
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
    (DefaultFunctionQuib, '__round__', round),
    (DefaultFunctionQuib, '__trunc__', trunc),
    (DefaultFunctionQuib, '__floor__', floor),
    (DefaultFunctionQuib, '__ceil__', ceil),
]


ALL_OVERRIDES = ARITHMETIC_OVERRIDES + UNARY_OVERRIDES + ROUNDING_OVERRIDES + \
                COMPARISON_OVERRIDES


def _create_reverse_operator_wrapper(cls, forward_operator: Callable):
    quib_creator = cls.create_wrapper(forward_operator)

    def _wrapper(self, other):
        return quib_creator(other, self)

    return _wrapper


def override_quib_operators():
    """
    Make operators (and other magic methods) on quibs return quibs.
    Overriding __getattr__ does not suffice because lookup of magic methods does not go
    through the standard getattr process.
    See more here: https://docs.python.org/3/reference/datamodel.html#special-method-lookup
    """
    for cls, name, wrapped in ALL_OVERRIDES:
        assert name not in vars(Quib), name
        setattr(Quib, name, cls.create_wrapper(wrapped))

    for cls, name, wrapped in ARITHMETIC_OVERRIDES:
        rname = '__r' + name[2:]
        setattr(Quib, rname, _create_reverse_operator_wrapper(cls, wrapped))
