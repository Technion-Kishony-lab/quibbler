import functools
import math
import operator
from dataclasses import dataclass

from typing import List

from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls
from pyquibbler.quib import Quib
from pyquibbler.translation.translators.elementwise.elementwise_translator import BackwardsElementwisePathTranslator, \
    ForwardsElementwisePathTranslator
from pyquibbler.utilities.operators_with_reverse import REVERSE_OPERATOR_NAMES_TO_FUNCS


@dataclass
class OperatorOverride(FuncOverride):
    SPECIAL_FUNCS = {
        '__round__': round,
        '__ceil__': math.ceil,
        '__trunc__': math.trunc,
        '__floor__': math.floor,
        '__getitem__': operator.getitem
    }

    def _get_func_from_module_or_cls(self):
        if self.func_name in self.SPECIAL_FUNCS:
            return self.SPECIAL_FUNCS[self.func_name]
        if self.func_name in REVERSE_OPERATOR_NAMES_TO_FUNCS:
            return REVERSE_OPERATOR_NAMES_TO_FUNCS[self.func_name]
        return getattr(operator, self.func_name)


operator_override = functools.partial(override_with_cls, OperatorOverride, Quib)


def with_reverse_operator_overrides(name, data_source_indexes: List = None, inverters=None,
                                    backwards_path_translators: List = None, forwards_path_translators: List = None):
    rname = '__r' + name[2:]

    return [operator_override(name, data_source_indexes,
                              inverters=inverters,
                              backwards_path_translators=backwards_path_translators,
                              forwards_path_translators=forwards_path_translators),
            operator_override(rname, data_source_indexes,
                              inverters=inverters,
                              backwards_path_translators=backwards_path_translators,
                              forwards_path_translators=forwards_path_translators)
            ]


elementwise_operator_override = \
    functools.partial(operator_override,
                      backwards_path_translators=[BackwardsElementwisePathTranslator],
                      forwards_path_translators=[ForwardsElementwisePathTranslator])

with_reverse_elementwise_operator_overrides = \
    functools.partial(with_reverse_operator_overrides,
                      backwards_path_translators=[BackwardsElementwisePathTranslator],
                      forwards_path_translators=[ForwardsElementwisePathTranslator])


def elementwise_translators():
    from pyquibbler.translation.translators.elementwise.elementwise_translator import \
        BackwardsElementwisePathTranslator, ForwardsElementwisePathTranslator

    return dict(
        backwards_path_translators=[BackwardsElementwisePathTranslator],
        forwards_path_translators=[ForwardsElementwisePathTranslator]
    )
