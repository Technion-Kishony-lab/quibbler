from functools import partial
from typing import Tuple, Optional, Dict, Callable

import numpy as np

from pyquibbler.env import ALLOW_ARRAY_WITH_DTYPE_OBJECT

from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override, override_with_cls
from pyquibbler.utilities.general_utils import Args, Kwargs

from .func_definitions import FUNC_DEFINITION_RANDOM, FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE, \
    FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_MANY, FUNC_DEFINITION_SHAPE_ONLY, FUNC_DEFINITION_AXIS_ALL_TO_ALL, \
    FUNC_DEFINITION_ACCUMULATION, FUNC_DEFINITION_REDUCTION, FUNC_DEFINITION_FILE_LOADING, \
    FUNC_DEFINITION_UNARY_ELEMENTWISE, FUNC_DEFINITION_BINARY_ELEMENTWISE

from .inverse_functions import RawInverseFunc, InverseFunc


class NumpyArrayOverride(FuncOverride):

    # We do not create quib for np.array([quib, ...], dtype=object).
    # This way, we can allow building object arrays containing quibs.

    @staticmethod
    def should_create_quib(func: Callable, args: Args, kwargs: Kwargs):
        return ALLOW_ARRAY_WITH_DTYPE_OBJECT or kwargs.get('dtype', None) is not object


numpy_override = partial(override, np)


def numpy_override_random(func_name):
    return override(module_or_cls=np.random,
                    func_name=func_name,
                    base_func_definition=FUNC_DEFINITION_RANDOM,
                    result_type_or_type_translators=np.ndarray,
                    )


def numpy_override_read_file(func_name):
    return numpy_override(func_name=func_name,
                          base_func_definition=FUNC_DEFINITION_FILE_LOADING,
                          result_type_or_type_translators=np.ndarray,
                          )


numpy_array_override = partial(override_with_cls, NumpyArrayOverride, np,
                               base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE)


def numpy_override_dataless(func_name, result_type_or_type_translators):
    return numpy_override(func_name, result_type_or_type_translators=result_type_or_type_translators)


def numpy_override_transpositional_one_to_one(func_name, data_source_arguments, result_type_or_type_translators):
    return numpy_override(func_name,
                          base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE,
                          data_source_arguments=data_source_arguments,
                          result_type_or_type_translators=result_type_or_type_translators)


def numpy_override_transpositional_one_to_many(func_name, data_source_arguments, result_type_or_type_translators):
    return numpy_override(func_name,
                          base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_MANY,
                          data_source_arguments=data_source_arguments,
                          result_type_or_type_translators=result_type_or_type_translators)


def numpy_override_accumulation(func_name):
    return numpy_override(func_name=func_name,
                          base_func_definition=FUNC_DEFINITION_ACCUMULATION,
                          result_type_or_type_translators=np.ndarray)


def numpy_override_reduction(func_name):
    return numpy_override(func_name=func_name,
                          base_func_definition=FUNC_DEFINITION_REDUCTION)


def numpy_override_axis_wise(func_name):
    return numpy_override(func_name=func_name,
                          result_type_or_type_translators=np.ndarray,
                          base_func_definition=FUNC_DEFINITION_AXIS_ALL_TO_ALL)


def numpy_override_shape_only(func_name, data_source_arguments, result_type_or_type_translators):
    return numpy_override(func_name=func_name,
                          base_func_definition=FUNC_DEFINITION_SHAPE_ONLY,
                          data_source_arguments=data_source_arguments,
                          result_type_or_type_translators=result_type_or_type_translators)


def numpy_override_array(func_name, data_sources, result_type):
    return numpy_array_override(func_name,
                                data_source_arguments=data_sources,
                                result_type_or_type_translators=result_type)


UNARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS: Dict[str, InverseFunc] = {}
BINARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS: Dict[str, Tuple[Optional[InverseFunc]]] = {}


def get_binary_inverse_funcs_for_func(func_name: str) -> Tuple[Optional[InverseFunc]]:
    return BINARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name]


def get_unary_inverse_funcs_for_func(func_name: str) -> InverseFunc:
    return UNARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name]


def binary_elementwise(func_name: str, raw_inverse_funcs: Tuple[Optional[RawInverseFunc]]):
    func = getattr(np, func_name)
    inverse_funcs = tuple(None if raw_inverse_func is None else InverseFunc.from_raw_inverse_func(raw_inverse_func)
                          for raw_inverse_func in raw_inverse_funcs)

    BINARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name] = inverse_funcs

    return numpy_override(
        func_name=func_name,
        base_func_definition=FUNC_DEFINITION_BINARY_ELEMENTWISE,
        func=func,
        inverse_funcs=inverse_funcs,
    )


def unary_elementwise(func_name: str, raw_inverse_func: Optional[RawInverseFunc]):
    func = getattr(np, func_name)
    inverse_func = None if raw_inverse_func is None else InverseFunc.from_raw_inverse_func(raw_inverse_func)

    UNARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name] = inverse_func

    return numpy_override(
        func_name=func_name,
        base_func_definition=FUNC_DEFINITION_UNARY_ELEMENTWISE,
        func=func,
        inverse_funcs=(inverse_func, ),
    )
