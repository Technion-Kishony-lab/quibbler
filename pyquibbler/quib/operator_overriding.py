"""
Override Quib operators by replacing magic methods with function quib wrappers that wrap operator function
from the operator module.
We have to use the operator functions in order to allow builtin operator functionality:
1. Calling inverse arithmetic operations when the normal ones return NotImplemented
2. Cases where a magic method is not present on a built-in type but the operator works anyway (e.g. float.__ceil__).
"""
import functools
import operator
from functools import wraps
from math import ceil, floor, trunc
from typing import Callable, Optional, Tuple, Type

from .function_quibs import DefaultFunctionQuib
from .function_quibs.elementwise_function_quib import ElementWiseFunctionQuib
from .quib import Quib


def operator_override(operator_name: str, cls: Type[DefaultFunctionQuib] = None) -> Tuple[Type[DefaultFunctionQuib],
                                                                                          str, Callable]:
    cls = cls or DefaultFunctionQuib
    return cls, operator_name, getattr(operator, operator_name)


ARITHMETIC_OVERRIDES = [
    operator_override('__add__', ElementWiseFunctionQuib),
    operator_override('__sub__', ElementWiseFunctionQuib),
    operator_override('__mul__', ElementWiseFunctionQuib),
    operator_override('__matmul__'),
    operator_override('__truediv__', ElementWiseFunctionQuib),
    operator_override('__floordiv__'),
    operator_override('__mod__', ElementWiseFunctionQuib),
    (DefaultFunctionQuib, '__divmod__', divmod),
    operator_override('__pow__', ElementWiseFunctionQuib),
    operator_override('__lshift__'),
    operator_override('__rshift__'),
    operator_override('__and__', ElementWiseFunctionQuib),
    operator_override('__xor__', ElementWiseFunctionQuib),
    operator_override('__or__', ElementWiseFunctionQuib),
]

UNARY_OVERRIDES = [
    operator_override('__neg__',ElementWiseFunctionQuib),
    operator_override('__pos__',ElementWiseFunctionQuib),
    operator_override('__abs__',ElementWiseFunctionQuib),
    operator_override('__invert__'),
]

COMPARISON_OVERRIDES = [
    operator_override('__lt__',ElementWiseFunctionQuib),
    operator_override('__gt__',ElementWiseFunctionQuib),
    operator_override('__ge__',ElementWiseFunctionQuib),
    operator_override('__le__',ElementWiseFunctionQuib),
]

ROUNDING_OVERRIDES = [
    (ElementWiseFunctionQuib, '__round__', round),
    (ElementWiseFunctionQuib, '__trunc__', trunc),
    (ElementWiseFunctionQuib, '__floor__', floor),
    (ElementWiseFunctionQuib, '__ceil__', ceil),
]


ALL_OVERRIDES = ARITHMETIC_OVERRIDES + UNARY_OVERRIDES + ROUNDING_OVERRIDES + \
                COMPARISON_OVERRIDES


def _create_inverse_operator_wrapper(cls, forward_operator: Callable):
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
        setattr(Quib, rname, _create_inverse_operator_wrapper(cls, wrapped))
