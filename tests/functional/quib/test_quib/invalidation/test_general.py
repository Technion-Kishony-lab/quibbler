from unittest import mock

import numpy as np
import pytest

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.graphics import UpdateType


def test_quib_does_not_request_shape_or_parents_shapes_on_first_attempt(create_mock_quib):
    parent_quib = create_quib(func=mock.Mock(), args=(1,))
    quib = create_quib(func=lambda a: a, args=(parent_quib,))
    forwards_path_translator = mock.Mock()
    forwards_path_translator.return_value.translate.return_value = {}
    add_definition_for_function(func=quib.func, function_definition=create_func_definition(
        raw_data_source_arguments=[0], forwards_path_translators=[forwards_path_translator]))

    parent_quib.handler.invalidate_and_redraw_at_path([])

    assert parent_quib.func.call_count == 0


@pytest.mark.regression
def test_diamond_invalidation_with_changing_shape(create_quib_with_return_value):
    a = create_quib_with_return_value(5, allow_overriding=True)
    b = np.arange(a)
    c = np.arange(a)
    d = c & b
    e = d * 2
    # We need to get value so we all quibs start in valid status (thereby checking if invalidation actually goes
    # through correctly without raising exceptions)
    e.get_value()

    # This previously raised an exception
    a.assign(10)

    assert np.array_equal(e.get_value(), np.arange(10) * 2)