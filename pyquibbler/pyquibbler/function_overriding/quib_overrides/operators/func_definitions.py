from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition

from pyquibbler.inversion.inverters.list_operators import ListOperatorInverter
from pyquibbler.path_translation.translators.list_operators import \
    ListOperatorBackwardsPathTranslator, ListOperatorForwardsPathTranslator

from pyquibbler.function_overriding.third_party_overriding.numpy.func_definitions import \
    FUNC_DEFINITION_BINARY_ELEMENTWISE

FUNC_DEFINITION_BINARY_ELEMENTWISE_AND_LIST = create_or_reuse_func_definition(
    base_func_definition=FUNC_DEFINITION_BINARY_ELEMENTWISE,
    backwards_path_translators=[ListOperatorBackwardsPathTranslator,
                                *FUNC_DEFINITION_BINARY_ELEMENTWISE.backwards_path_translators],
    forwards_path_translators=[ListOperatorForwardsPathTranslator,
                               *FUNC_DEFINITION_BINARY_ELEMENTWISE.forwards_path_translators],
    inverters=[ListOperatorInverter] + FUNC_DEFINITION_BINARY_ELEMENTWISE.inverters)
