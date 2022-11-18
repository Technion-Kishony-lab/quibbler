from pyquibbler.function_overriding.third_party_overriding.numpy.inverse_functions import InverseFunc
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

from pyquibbler.path_translation.translators.elementwise import \
    UnaryElementwiseNoShapeBackwardsPathTranslator
from pyquibbler.type_translation.translators import ElementwiseTypeTranslator

from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition, ElementWiseFuncDefinition

"""
Basic func definitions
"""


def identity(x):
    return x


FUNC_DEFINITION_RANDOM = create_or_reuse_func_definition(
    is_random=True)

FUNC_DEFINITION_FILE_LOADING = create_or_reuse_func_definition(
    is_file_loading=True)

FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE = create_or_reuse_func_definition(
    raw_data_source_arguments=[0],
    inverters=[TranspositionalOneToOneInverter],
    backwards_path_translators=[TranspositionalBackwardsPathTranslator],
    forwards_path_translators=[TranspositionalForwardsPathTranslator])

FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_MANY = create_or_reuse_func_definition(
    base_func_definition=FUNC_DEFINITION_TRANSPOSITIONAL_ONE_TO_ONE,
    inverters=[TranspositionalOneToManyInverter])

FUNC_DEFINITION_ACCUMULATION = create_or_reuse_func_definition(
    raw_data_source_arguments=[0],
    backwards_path_translators=[AxisAccumulationBackwardsPathTranslator],
    forwards_path_translators=[AxisAccumulationForwardsPathTranslator])

FUNC_DEFINITION_REDUCTION = create_or_reuse_func_definition(
    raw_data_source_arguments=[0],
    backwards_path_translators=[AxisReductionBackwardsPathTranslator],
    forwards_path_translators=[AxisReductionForwardsPathTranslator])

FUNC_DEFINITION_AXIS_ALL_TO_ALL = create_or_reuse_func_definition(
    raw_data_source_arguments=[0],
    backwards_path_translators=[AxisAllToAllBackwardsPathTranslator],
    forwards_path_translators=[AxisAllToAllForwardsPathTranslator])

FUNC_DEFINITION_SHAPE_ONLY = create_or_reuse_func_definition(
    raw_data_source_arguments=[0],
    backwards_path_translators=[ShapeOnlyBackwardsPathTranslator],
    forwards_path_translators=[ShapeOnlyForwardsPathTranslator])

FUNC_DEFINITION_UNARY_ELEMENTWISE = create_or_reuse_func_definition(
    raw_data_source_arguments=[0],
    backwards_path_translators=[UnaryElementwiseNoShapeBackwardsPathTranslator,
                                UnaryElementwiseBackwardsPathTranslator],
    forwards_path_translators=[UnaryElementwiseForwardsPathTranslator],
    result_type_or_type_translators=[ElementwiseTypeTranslator],
    inverters=[UnaryElementwiseNoShapeInverter, UnaryElementwiseInverter],
    func_definition_cls=ElementWiseFuncDefinition)

FUNC_DEFINITION_BINARY_ELEMENTWISE = create_or_reuse_func_definition(
    raw_data_source_arguments=[0, 1],
    backwards_path_translators=[BinaryElementwiseBackwardsPathTranslator],
    forwards_path_translators=[BinaryElementwiseForwardsPathTranslator],
    result_type_or_type_translators=[ElementwiseTypeTranslator],
    inverters=[BinaryElementwiseInverter],
    func_definition_cls=ElementWiseFuncDefinition)

FUNC_DEFINITION_ELEMENTWISE_IDENTITY = create_or_reuse_func_definition(
    base_func_definition=FUNC_DEFINITION_UNARY_ELEMENTWISE,
    func=identity,
    inverse_funcs=(InverseFunc.from_raw_inverse_func(identity), ),
)
