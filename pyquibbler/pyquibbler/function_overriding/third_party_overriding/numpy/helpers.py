from functools import partial
from typing import Tuple, Optional, Dict

import numpy as np

from pyquibbler.env import ALLOW_ARRAY_WITH_DTYPE_OBJECT

from pyquibbler.function_overriding.function_override import FuncOverride
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override, override_with_cls

from pyquibbler.path_translation.translators import \
    TranspositionalBackwardsPathTranslator, TranspositionalForwardsPathTranslator, \
    AxisAccumulationBackwardsPathTranslator, AxisAccumulationForwardsPathTranslator, \
    AxisReductionBackwardsPathTranslator, AxisReductionForwardsPathTranslator, \
    AxisAllToAllBackwardsPathTranslator, AxisAllToAllForwardsPathTranslator, \
    ShapeOnlyBackwardsPathTranslator, ShapeOnlyForwardsPathTranslator, \
    BinaryElementwiseBackwardsPathTranslator, BinaryElementwiseForwardsPathTranslator, \
    UnaryElementwiseBackwardsPathTranslator, UnaryElementwiseForwardsPathTranslator

from pyquibbler.inversion.inverters.transpositional import \
    TranspositionalOneToManyInverter, TranspositionalOneToOneInverter
from pyquibbler.inversion.inverters.elementwise import BinaryElementwiseInverter, UnaryElementwiseInverter
from pyquibbler.inversion.inverters.elementwise_single_arg_no_shape import UnaryElementwiseNoShapeInverter

from pyquibbler.function_definitions.func_definition import ElementWiseFuncDefinition, create_or_reuse_func_definition
from pyquibbler.path_translation.translators.elementwise import \
    UnaryElementwiseNoShapeBackwardsPathTranslator
from pyquibbler.type_translation.translators import ElementwiseTypeTranslator

from .inverse_functions import RawInverseFunc, InverseFunc


class NumpyArrayOverride(FuncOverride):

    # We do not create quib for np.array([quib, ...], dtype=object).
    # This way, we can allow building object arrays containing quibs.

    @staticmethod
    def should_create_quib(func, args, kwargs):
        return ALLOW_ARRAY_WITH_DTYPE_OBJECT or kwargs.get('dtype', None) is not object


numpy_override = partial(override, np)

FUNC_DEFINITION_RANDOM = create_or_reuse_func_definition(is_random=True)

FUNC_DEFINITION_FILE_LOADING = create_or_reuse_func_definition(is_file_loading=True)

FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE = create_or_reuse_func_definition(raw_data_source_arguments=[0], inverters=[
    TranspositionalOneToOneInverter], backwards_path_translators=[TranspositionalBackwardsPathTranslator],
                                                                             forwards_path_translators=[
                                                                                 TranspositionalForwardsPathTranslator])

FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_MANY = create_or_reuse_func_definition(
    base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE, inverters=[TranspositionalOneToManyInverter])

FUNC_DEFINITION_ACCUMULATION = create_or_reuse_func_definition(raw_data_source_arguments=[0],
                                                               backwards_path_translators=[
                                                                   AxisAccumulationBackwardsPathTranslator],
                                                               forwards_path_translators=[
                                                                   AxisAccumulationForwardsPathTranslator])

FUNC_DEFINITION_REDUCTION = create_or_reuse_func_definition(raw_data_source_arguments=[0], backwards_path_translators=[
    AxisReductionBackwardsPathTranslator], forwards_path_translators=[AxisReductionForwardsPathTranslator])

FUNC_DEFINITION_AXIS_ALL_TO_ALL = create_or_reuse_func_definition(raw_data_source_arguments=[0],
                                                                  backwards_path_translators=[
                                                                      AxisAllToAllBackwardsPathTranslator],
                                                                  forwards_path_translators=[
                                                                      AxisAllToAllForwardsPathTranslator])

FUNC_DEFINITION_SHAPE_ONLY = create_or_reuse_func_definition(raw_data_source_arguments=[0], backwards_path_translators=[
    ShapeOnlyBackwardsPathTranslator], forwards_path_translators=[ShapeOnlyForwardsPathTranslator])

numpy_override_random = partial(override, np.random, base_func_definition=FUNC_DEFINITION_RANDOM)

numpy_override_read_file = partial(numpy_override, base_func_definition=FUNC_DEFINITION_FILE_LOADING)

numpy_override_transpositional_one_to_many = partial(numpy_override,
                                                     base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_MANY)

numpy_override_transpositional_one_to_one = partial(numpy_override,
                                                    base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE)

numpy_array_override = partial(override_with_cls, NumpyArrayOverride, np,
                               base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE)

numpy_override_accumulation = partial(numpy_override, base_func_definition=FUNC_DEFINITION_ACCUMULATION)
numpy_override_reduction = partial(numpy_override, base_func_definition=FUNC_DEFINITION_REDUCTION)
numpy_override_axis_wise = partial(numpy_override, base_func_definition=FUNC_DEFINITION_AXIS_ALL_TO_ALL)
numpy_override_shape_only = partial(numpy_override, base_func_definition=FUNC_DEFINITION_SHAPE_ONLY)

UNARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS: Dict[str, InverseFunc] = {}
BINARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS: Dict[str, Tuple[Optional[InverseFunc]]] = {}

BINARY_ELEMENTWISE_INVERTERS = [BinaryElementwiseInverter]
UNARY_ELEMENTWISE_INVERTERS = [UnaryElementwiseNoShapeInverter, UnaryElementwiseInverter]

UNARY_ELEMENTWISE_BACKWARDS_TRANSLATORS = [UnaryElementwiseNoShapeBackwardsPathTranslator,
                                           UnaryElementwiseBackwardsPathTranslator]


def get_binary_inverse_funcs_for_func(func_name: str) -> Tuple[Optional[InverseFunc]]:
    return BINARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name]


def get_unary_inverse_funcs_for_func(func_name: str) -> InverseFunc:
    return UNARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name]


def binary_elementwise(func_name: str, raw_inverse_funcs: Tuple[Optional[RawInverseFunc]]):
    inverse_funcs = tuple(None if raw_inverse_func is None else InverseFunc.from_raw_inverse_func(raw_inverse_func)
                          for raw_inverse_func in raw_inverse_funcs)

    BINARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name] = inverse_funcs

    return numpy_override(
        func_name=func_name,
        data_source_arguments=[0, 1],
        backwards_path_translators=[BinaryElementwiseBackwardsPathTranslator],
        forwards_path_translators=[BinaryElementwiseForwardsPathTranslator],
        result_type_or_type_translators=[ElementwiseTypeTranslator],
        inverters=BINARY_ELEMENTWISE_INVERTERS,
        inverse_funcs=inverse_funcs,
        func_definition_cls=ElementWiseFuncDefinition,
    )


def unary_elementwise(func_name: str, raw_inverse_func: Optional[RawInverseFunc]):

    inverse_func = None if raw_inverse_func is None else InverseFunc.from_raw_inverse_func(raw_inverse_func)

    UNARY_ELEMENTWISE_FUNCS_TO_INVERSE_FUNCS[func_name] = inverse_func

    return numpy_override(
        func_name=func_name,
        data_source_arguments=[0],
        backwards_path_translators=UNARY_ELEMENTWISE_BACKWARDS_TRANSLATORS,
        forwards_path_translators=[UnaryElementwiseForwardsPathTranslator],
        result_type_or_type_translators=[ElementwiseTypeTranslator],
        inverters=UNARY_ELEMENTWISE_INVERTERS,
        inverse_funcs=(inverse_func, ),
        func_definition_cls=ElementWiseFuncDefinition,
    )
