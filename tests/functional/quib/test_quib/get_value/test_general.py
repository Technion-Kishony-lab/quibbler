from unittest import mock

from pyquibbler import CachingOptions
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import FuncDefinition, create_func_definition
from pyquibbler.quib.factory import create_quib


def test_quib_does_not_request_shape_or_parents_shapes_on_first_attempt(create_mock_quib):
    parent = create_mock_quib()
    quib = create_quib(func=lambda a: a, args=(parent,))
    backwards_path_translator = mock.Mock()
    backwards_path_translator.return_value.translate.return_value = {}
    add_definition_for_function(func=quib.func, function_definition=create_func_definition(
        raw_data_source_arguments=[0], backwards_path_translators=[backwards_path_translator]))

    quib.get_value()

    assert parent.get_value_valid_at_path.call_count == 1
