import functools
import math
import operator
from dataclasses import dataclass

from typing import List, Optional, Callable, Tuple

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


#operator_override = functools.partial(override_with_cls, OperatorOverride, Quib)


def              operator_override(name,
                                    data_source_indexes: Optional[List] = None,
                                    inverters: Optional[List] = None,
                                    backwards_path_translators: Optional[List] = None,
                                    forwards_path_translators: Optional[List] = None,
                                    inverse_funcs: Optional[Tuple[Callable]] = None,
                                    with_reverse: bool = False,
                                    ):
    names = [name]
    if with_reverse:
        names.append('__r' + name[2:])

    overrides = [override_with_cls(OperatorOverride, Quib,
                                   func_name, data_source_indexes,
                                   inverters=inverters,
                                   backwards_path_translators=backwards_path_translators,
                                   forwards_path_translators=forwards_path_translators,
                                   inverse_func_with_input=None if not inverse_funcs else inverse_funcs[0],
                                   inverse_func_without_input=None if not inverse_funcs else inverse_funcs[1],
                                   )
                 for func_name in names]

    if with_reverse:
        return overrides
    return overrides[0]



with_reverse_operator_overrides = functools.partial(operator_override, with_reverse=True)

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
