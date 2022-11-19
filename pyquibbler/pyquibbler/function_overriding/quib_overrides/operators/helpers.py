import math
import operator
from dataclasses import dataclass

from typing import List, Optional, Tuple

from pyquibbler.quib.quib import Quib

from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override_with_cls
from pyquibbler.utilities.operators_with_reverse import REVERSE_OPERATOR_NAMES_TO_FUNCS

from pyquibbler.function_overriding.third_party_overriding.numpy.func_definitions import \
    FUNC_DEFINITION_UNARY_ELEMENTWISE, FUNC_DEFINITION_BINARY_ELEMENTWISE
from .func_definitions import FUNC_DEFINITION_BINARY_ELEMENTWISE_AND_LIST
from pyquibbler.function_overriding.third_party_overriding.numpy.inverse_functions import InverseFunc

SPECIAL_FUNCS = {
    '__round__': round,
    '__ceil__': math.ceil,
    '__trunc__': math.trunc,
    '__floor__': math.floor,
    '__getitem__': operator.getitem
}


def get_operator_func(func_name):
    if func_name in SPECIAL_FUNCS:
        return SPECIAL_FUNCS[func_name]
    if func_name in REVERSE_OPERATOR_NAMES_TO_FUNCS:
        return REVERSE_OPERATOR_NAMES_TO_FUNCS[func_name]
    return getattr(operator, func_name)


@dataclass
class OperatorOverride(FuncOverride):
    def _get_func_from_module_or_cls(self):
        return get_operator_func(self.func_name)


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
                             func_name,
                             data_source_arguments=data_source_indexes,
                             inverters=inverters,
                             backwards_path_translators=backwards_path_translators,
                             forwards_path_translators=forwards_path_translators,
                             )


def binary_operator_override(func_name,
                             inverse_funcs: Tuple[Optional[InverseFunc]] = None,
                             is_reverse: bool = False,
                             ):

    func = get_operator_func(func_name)

    # add special translators/invertors for list addition and multiplication:
    if func_name in ['__add__', '__mul__']:
        base_func_definition = FUNC_DEFINITION_BINARY_ELEMENTWISE_AND_LIST
    else:
        base_func_definition = FUNC_DEFINITION_BINARY_ELEMENTWISE

    if is_reverse:
        func_name = '__r' + func_name[2:]
        inverse_funcs = inverse_funcs[-1::-1]

    return override_with_cls(OperatorOverride, Quib,
                             func_name,
                             base_func_definition=base_func_definition,
                             func=func,
                             inverse_funcs=inverse_funcs,
                             is_operator=True,
                             )


def unary_operator_override(func_name,
                            inverse_func: InverseFunc,
                            ):
    func = get_operator_func(func_name)
    return override_with_cls(OperatorOverride, Quib,
                             func_name,
                             base_func_definition=FUNC_DEFINITION_UNARY_ELEMENTWISE,
                             func=func,
                             inverse_funcs=(inverse_func, ),
                             is_operator=True,
                             )
