import math
import operator
from dataclasses import dataclass

from typing import List, Optional, Callable, Tuple

from pyquibbler.function_definitions.func_definition import ElementWiseFuncDefinition
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls
from pyquibbler.quib.quib import Quib
from pyquibbler.translation.translators.elementwise_translator import BackwardsElementwisePathTranslator, \
    ForwardsElementwisePathTranslator
from pyquibbler.utilities.operators_with_reverse import REVERSE_OPERATOR_NAMES_TO_FUNCS
from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import ELEMENTWISE_INVERTERS


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


def operator_override(func_name,
                      data_source_indexes: Optional[List] = None,
                      inverters: Optional[List] = None,
                      backwards_path_translators: Optional[List] = None,
                      forwards_path_translators: Optional[List] = None,
                      is_reverse: bool = False,
                      ):
    if is_reverse:
        func_name = '__r' + func_name[2:]

    return override_with_cls(OperatorOverride, Quib,
                             func_name, data_source_indexes,
                             inverters=inverters,
                             backwards_path_translators=backwards_path_translators,
                             forwards_path_translators=forwards_path_translators,
                             )


def elementwise_operator_override(func_name,
                                  data_source_indexes: Optional[List] = None,
                                  inverse_funcs: Optional[Tuple[Callable]] = None,
                                  is_reverse: bool = False,
                                  ):
    if is_reverse:
        func_name = '__r' + func_name[2:]
        inverse_funcs = tuple({0: inv_func[1], 1: inv_func[0]} if isinstance(inv_func, dict)
                              else inv_func for inv_func in inverse_funcs)

    return override_with_cls(OperatorOverride, Quib,
                             func_name, data_source_indexes,
                             inverters=ELEMENTWISE_INVERTERS,
                             backwards_path_translators=[BackwardsElementwisePathTranslator],
                             forwards_path_translators=[ForwardsElementwisePathTranslator],
                             inverse_func_with_input=None if not inverse_funcs else inverse_funcs[0],
                             inverse_func_without_input=None if not inverse_funcs else inverse_funcs[1],
                             func_definition_cls=ElementWiseFuncDefinition,
                             )
