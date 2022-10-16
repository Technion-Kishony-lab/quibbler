import math
import operator
from dataclasses import dataclass

from typing import List, Optional, Callable, Tuple

from pyquibbler.function_definitions.func_definition import \
    UnaryElementWiseFuncDefinition, BinaryElementWiseFuncDefinition
from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls
from pyquibbler.quib.quib import Quib
from pyquibbler.path_translation.translators.elementwise_translator import \
    BinaryElementwiseBackwardsPathTranslator, BinaryElementwiseForwardsPathTranslator, \
    UnaryElementwiseForwardsPathTranslator
from pyquibbler.type_translation.translators import ElementwiseTypeTranslator
from pyquibbler.path_translation.translators.list_addition_translator import \
    ListAdditionBackwardsPathTranslator, ListAdditionForwardsPathTranslator

from pyquibbler.utilities.operators_with_reverse import REVERSE_OPERATOR_NAMES_TO_FUNCS
from pyquibbler.function_overriding.third_party_overriding.numpy.helpers import \
    BINARY_ELEMENTWISE_INVERTERS, UNARY_ELEMENTWISE_INVERTERS, UNARY_ELEMENTWISE_BACKWARDS_TRANSLATORS


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


def binary_operator_override(func_name,
                             inverse_funcs: Optional[Tuple[Callable]] = None,
                             is_reverse: bool = False,
                             add_list_translation: bool = False,
                             ):
    if is_reverse:
        func_name = '__r' + func_name[2:]
        inverse_funcs = {0: inverse_funcs[1], 1: inverse_funcs[0]}

    backwards_path_translators = [BinaryElementwiseBackwardsPathTranslator]
    forwards_path_translators = [BinaryElementwiseForwardsPathTranslator]
    if add_list_translation:
        backwards_path_translators.append(ListAdditionBackwardsPathTranslator)
        forwards_path_translators.append(ListAdditionForwardsPathTranslator)

    return override_with_cls(OperatorOverride, Quib,
                             func_name,
                             data_source_arguments=[0, 1],
                             inverters=BINARY_ELEMENTWISE_INVERTERS,
                             backwards_path_translators=backwards_path_translators,
                             forwards_path_translators=forwards_path_translators,
                             result_type_or_type_translators=[ElementwiseTypeTranslator],
                             inverse_funcs=inverse_funcs,
                             func_definition_cls=BinaryElementWiseFuncDefinition,
                             )


def unary_operator_override(func_name,
                                        inverse_func_and_is_input_required: Tuple[Callable, bool] = None,
                                        ):
    inverse_func, inverse_func_requires_input = inverse_func_and_is_input_required
    return override_with_cls(OperatorOverride, Quib,
                             func_name,
                             data_source_arguments=[0],
                             inverters=UNARY_ELEMENTWISE_INVERTERS,
                             backwards_path_translators=UNARY_ELEMENTWISE_BACKWARDS_TRANSLATORS,
                             forwards_path_translators=[UnaryElementwiseForwardsPathTranslator],
                             result_type_or_type_translators=[ElementwiseTypeTranslator],
                             inverse_func=inverse_func,
                             inverse_func_requires_input=inverse_func_requires_input,
                             func_definition_cls=UnaryElementWiseFuncDefinition,
                             )
