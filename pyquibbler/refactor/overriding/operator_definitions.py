import math
import operator
from dataclasses import dataclass
from inspect import signature

from typing import Callable, List

from pyquibbler.refactor.inversion.inverters.getitem_inverter import GetItemInverter
from pyquibbler.refactor.overriding.override_definition import OverrideDefinition
from pyquibbler.refactor.overriding.types import IndexArgument, KeywordArgument

from pyquibbler.refactor.translation.translators import BackwardsGetItemTranslator
from pyquibbler.refactor.translation.translators.transpositional.getitem_translator import ForwardsGetItemTranslator


# TODO: Make order here- why is it one class for mathematical operations that have reversed, etc
def get_reversed_func(func: Callable):
    def _reversed(q, o):
        return func(o, q)
    return _reversed


@dataclass
class OperatorOverrideDefinition(OverrideDefinition):
    SPECIAL_FUNCS = {
        '__round__': round,
        '__ceil__': math.ceil,
        '__trunc__': math.trunc,
        '__floor__': math.floor,
        '__getitem__': operator.getitem
    }
    is_reversed: bool = False

    def _get_func_from_module_or_cls(self):
        if self.func_name in self.SPECIAL_FUNCS:
            return self.SPECIAL_FUNCS[self.func_name]

        if self.is_reversed:
            regular_func_name = f'__{self.func_name[3:]}'
            return get_reversed_func(getattr(operator, regular_func_name))

        return getattr(operator, self.func_name)

    #
    # def override(self):
    #     super(OperatorOverrideDefinition, self).override()
    #     if self.override_reverse_operator:
    #         reverse_func = self.quib_supporting_func(
    #             lambda quib, other: self._get_func_from_module_or_cls()(other, quib)
    #         )
    #         rname = '__r' + self.func_name[2:]
    #         setattr(self.module_or_cls, rname, reverse_func)


def operator_definition(name, data_source_indexes: List = None, inverters: List = None,
                        backwards_path_translators: List = None, forwards_path_translators: List = None):
    data_source_indexes = data_source_indexes or list(signature(getattr(operator, name)).parameters.keys())
    from pyquibbler.refactor.quib.quib import Quib
    return OperatorOverrideDefinition(
        func_name=name,
        data_source_arguments={IndexArgument(i) if isinstance(i, int) else KeywordArgument(i)
                               for i in (data_source_indexes or [])},
        module_or_cls=Quib,
        inverters=inverters,
        backwards_path_translators=backwards_path_translators,
        forwards_path_translators=forwards_path_translators
    )


def with_reverse_operator_definition(name, data_source_indexes: List = None):
    rname = '__r' + name[2:]

    from pyquibbler.refactor.quib.quib import Quib
    return [operator_definition(name, data_source_indexes), OperatorOverrideDefinition(
        func_name=rname,
        data_source_arguments={IndexArgument(i) for i in (data_source_indexes or [])},
        module_or_cls=Quib,
        is_reversed=True
    )]


def get_arithmetic_definitions():
    return [
        *with_reverse_operator_definition('__add__'),
        *with_reverse_operator_definition('__sub__'),
        *with_reverse_operator_definition('__mul__'),
        operator_definition('__matmul__', []),
        *with_reverse_operator_definition('__truediv__'),
        *with_reverse_operator_definition('__floordiv__'),
        *with_reverse_operator_definition('__mod__'),
        *with_reverse_operator_definition('__pow__'),
        *with_reverse_operator_definition('__lshift__'),
        *with_reverse_operator_definition('__rshift__'),
        *with_reverse_operator_definition('__and__'),
        *with_reverse_operator_definition('__xor__'),
        *with_reverse_operator_definition('__or__'),
    ]


def get_unary_definitions():
    return [
        operator_definition('__neg__'),
        operator_definition('__pos__'),
        operator_definition('__abs__'),
        operator_definition('__invert__'),
    ]


def get_operator_definitions():

    comparison_definitions = [
        operator_definition('__lt__'),
        operator_definition('__gt__'),
        operator_definition('__ge__'),
        operator_definition('__le__'),
    ]


    rounding_definitions = [
        operator_definition('__round__', [0]),
        operator_definition('__trunc__', [0]),
        operator_definition('__floor__', [0]),
        operator_definition('__ceil__', [0]),
    ]

    return [*get_arithmetic_definitions(), *get_unary_definitions(), *comparison_definitions,
             *rounding_definitions, operator_definition(
            '__getitem__',
            data_source_indexes=[0],
            inverters=[GetItemInverter],
            backwards_path_translators=[BackwardsGetItemTranslator],
            forwards_path_translators=[ForwardsGetItemTranslator]
        )]
