import functools
import math
import operator
from dataclasses import dataclass
from inspect import signature
from operator import getitem

from typing import Callable, Set, List

from pyquibbler.overriding.definitions import OverrideDefinition
from pyquibbler.overriding.types import IndexArgument, KeywordArgument
from pyquibbler.quib.refactor.quib import Quib
from pyquibbler.quib.utils import iter_args_and_names_in_function_call


@dataclass
class OperatorOverrideDefinition(OverrideDefinition):
    SPECIAL_FUNCS = {
        '__round__': round,
        '__ceil__': math.ceil,
        '__trunc__': math.trunc,
        '__floor__': math.floor
    }
    override_reverse_operator: bool = False

    def _get_wrapped_func(self):
        if self.func_name in self.SPECIAL_FUNCS:
            return self.SPECIAL_FUNCS[self.func_name]
        return getattr(operator, self.func_name)

    def override(self):
        super(OperatorOverrideDefinition, self).override()
        if self.override_reverse_operator:
            reverse_func = self._create_func_to_maybe_create_quib(
                lambda quib, other: self._get_wrapped_func()(other, quib)
            )
            rname = '__r' + self.func_name[2:]
            setattr(self.module_or_cls, rname, reverse_func)


def operator_definition(name, data_source_indexes: List = None, override_reverse_operator: bool = False):
    data_source_indexes = data_source_indexes or list(signature(getattr(operator, name)).parameters.keys())
    return OperatorOverrideDefinition(
        func_name=name,
        data_source_arguments={IndexArgument(i) for i in (data_source_indexes or [])},
        module_or_cls=Quib,
        override_reverse_operator=override_reverse_operator
    )


with_reverse_operator_definition = functools.partial(operator_definition, override_reverse_operator=True)

ARITHMETIC_OPERATORS_DEFINITIONS = [
    with_reverse_operator_definition('__add__'),
    with_reverse_operator_definition('__sub__'),
    with_reverse_operator_definition('__mul__'),
    operator_definition('__matmul__', []),
    with_reverse_operator_definition('__truediv__'),
    with_reverse_operator_definition('__floordiv__'),
    with_reverse_operator_definition('__mod__'),
    with_reverse_operator_definition('__pow__'),
    with_reverse_operator_definition('__lshift__'),
    with_reverse_operator_definition('__rshift__'),
    with_reverse_operator_definition('__and__'),
    with_reverse_operator_definition('__xor__'),
    with_reverse_operator_definition('__or__'),
]

UNARY_OPERATORS_DEFINITIONS = [
    operator_definition('__neg__'),
    operator_definition('__pos__'),
    operator_definition('__abs__'),
    operator_definition('__invert__'),
]

COMPARISON_OVERRIDES = [
    operator_definition('__lt__'),
    operator_definition('__gt__'),
    operator_definition('__ge__'),
    operator_definition('__le__'),
]


ROUNDING_OVERRIDES = [
    operator_definition('__round__', [0]),
    operator_definition('__trunc__', [0]),
    operator_definition('__floor__', [0]),
    operator_definition('__ceil__', [0]),
]

OPERATOR_DEFINITIONS = [*ARITHMETIC_OPERATORS_DEFINITIONS, *UNARY_OPERATORS_DEFINITIONS, *COMPARISON_OVERRIDES,
                        *ROUNDING_OVERRIDES]
