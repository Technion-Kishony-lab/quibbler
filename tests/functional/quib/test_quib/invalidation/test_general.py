from unittest import mock

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib


def test_quib_does_not_request_shape_or_parents_shapes_on_first_attempt(create_mock_quib):
    def func(a):
        return a

    parent_quib = create_quib(func=mock.Mock(), args=(1,))
    quib = create_quib(func=func, args=(parent_quib,))
    forwards_path_translator = mock.Mock()
    forwards_path_translator.return_value.translate.return_value = {}
    add_definition_for_function(func=quib.func, function_definition=create_func_definition(
        forwards_path_translators=[forwards_path_translator],
        data_source_arguments=[0]
    ))

    parent_quib.invalidate_and_redraw_at_path([])

    assert parent_quib.func.call_count == 0
