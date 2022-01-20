import functools
import math
import operator
from dataclasses import dataclass

from typing import Callable, List

from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls
from pyquibbler.quib import Quib
from pyquibbler.translation.translators.elementwise.elementwise_translator import BackwardsElementwisePathTranslator, \
    ForwardsElementwisePathTranslator


def get_reversed_func(func: Callable):
    def _reversed(q, o):
        return func(o, q)
    return _reversed


@dataclass
class OperatorOverride(FuncOverride):
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


operator_override = functools.partial(override_with_cls, OperatorOverride, Quib)


def with_reverse_operator_overrides(name, data_source_indexes: List = None, inverters=None,
                                    backwards_path_translators: List = None, forwards_path_translators: List = None):
    rname = '__r' + name[2:]

    from pyquibbler.quib.quib import Quib
    return [operator_override(name, data_source_indexes, inverters=inverters,
                              backwards_path_translators=backwards_path_translators,
                              forwards_path_translators=forwards_path_translators), OperatorOverride(
        func_name=rname,
        module_or_cls=Quib,
        is_reversed=True,
        function_definition=create_func_definition(
            data_source_arguments=data_source_indexes,
            inverters=inverters or [],
            backwards_path_translators=backwards_path_translators,
            forwards_path_translators=forwards_path_translators
        )
    )]


elementwise_operator_override = functools.partial(operator_override,
                                                  backwards_path_translators=[BackwardsElementwisePathTranslator],
                                                  forwards_path_translators=[ForwardsElementwisePathTranslator])

with_reverse_elementwise_operator_overrides = functools.partial(with_reverse_operator_overrides,
                                                                backwards_path_translators=[
                                                                    BackwardsElementwisePathTranslator
                                                                ],
                                                                forwards_path_translators=[
                                                                    ForwardsElementwisePathTranslator
                                                                ])


def elementwise_translators():
    from pyquibbler.translation.translators.elementwise.elementwise_translator import \
        BackwardsElementwisePathTranslator, ForwardsElementwisePathTranslator

    return dict(
        backwards_path_translators=[BackwardsElementwisePathTranslator],
        forwards_path_translators=[ForwardsElementwisePathTranslator]
    )
