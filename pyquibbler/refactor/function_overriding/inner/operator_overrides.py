import math
import operator
from dataclasses import dataclass
from inspect import signature

from typing import Callable, List

import numpy as np

from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
from pyquibbler.refactor.function_overriding.function_override import FunctionOverride
from pyquibbler.refactor.function_overriding.third_party_overriding.numpy.elementwise_overrides import \
    get_inverter_for_func, create_elementwise_overrides
from pyquibbler.refactor.inversion.inverters.getitem_inverter import GetItemInverter

from pyquibbler.refactor.function_definitions.types import PositionalArgument, KeywordArgument


from pyquibbler.refactor.translation.translators import BackwardsGetItemTranslator
from pyquibbler.refactor.translation.translators.elementwise.elementwise_translator import \
    BackwardsElementwisePathTranslator, ForwardsElementwisePathTranslator
from pyquibbler.refactor.translation.translators.transpositional.getitem_translator import ForwardsGetItemTranslator


# TODO: Make order here- why is it one class for mathematical operations that have reversed, etc
def get_reversed_func(func: Callable):
    def _reversed(q, o):
        return func(o, q)
    return _reversed


@dataclass
class OperatorOverride(FunctionOverride):
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
    return OperatorOverride(
        func_name=name,
        module_or_cls=Quib,
        function_definition=create_function_definition(
            data_source_arguments=data_source_indexes,
            inverters=inverters,
            backwards_path_translators=backwards_path_translators,
            forwards_path_translators=forwards_path_translators
        )
    )


def with_reverse_operator_definition(name, data_source_indexes: List = None, inverters=None,
                                     backwards_path_translators: List = None, forwards_path_translators: List = None):
    rname = '__r' + name[2:]

    from pyquibbler.refactor.quib.quib import Quib
    return [operator_definition(name, data_source_indexes, inverters=inverters,
                                backwards_path_translators=backwards_path_translators,
                                forwards_path_translators=forwards_path_translators), OperatorOverride(
        func_name=rname,
        module_or_cls=Quib,
        is_reversed=True,
        function_definition=create_function_definition(
            data_source_arguments=data_source_indexes,
            inverters=inverters or [],
            backwards_path_translators=backwards_path_translators,
            forwards_path_translators=forwards_path_translators
        )
    )]


def get_arithmetic_definitions():
    # We need to create elementwise overrides to make sure we have inverters for our elementwise operators
    create_elementwise_overrides()

    return [
        *with_reverse_operator_definition('__add__', [0, 1], [get_inverter_for_func(np.add)],
                                          backwards_path_translators=[BackwardsElementwisePathTranslator],
                                          forwards_path_translators=[ForwardsElementwisePathTranslator]),
        *with_reverse_operator_definition('__sub__', [0, 1], [get_inverter_for_func(np.subtract)],
                                          backwards_path_translators=[BackwardsElementwisePathTranslator],
                                          forwards_path_translators=[ForwardsElementwisePathTranslator]),
        *with_reverse_operator_definition('__mul__',  [0, 1], [get_inverter_for_func(np.multiply)],
                                          backwards_path_translators=[BackwardsElementwisePathTranslator],
                                          forwards_path_translators=[ForwardsElementwisePathTranslator]),
        operator_definition('__matmul__', []),
        *with_reverse_operator_definition('__truediv__', [0, 1], [get_inverter_for_func(np.divide)],
                                          backwards_path_translators=[BackwardsElementwisePathTranslator],
                                          forwards_path_translators=[ForwardsElementwisePathTranslator]),
        *with_reverse_operator_definition('__floordiv__'),
        *with_reverse_operator_definition('__mod__'),
        *with_reverse_operator_definition('__pow__', [0, 1], [get_inverter_for_func(np.power)],
                                          backwards_path_translators=[BackwardsElementwisePathTranslator],
                                          forwards_path_translators=[ForwardsElementwisePathTranslator]),
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
