from unittest import mock

import numpy as np
import pytest

from pyquibbler import q
from pyquibbler.path import PathComponent
from tests.functional.quib.test_quib.get_value.test_apply_along_axis import parametrize_data
from tests.functional.quib.test_quib.get_value.utils import check_get_value_valid_at_path


@parametrize_data
@pytest.mark.parametrize(['axis', 'indices_to_get_value_at'], [
    (-1, 0),
    (0, 0),
    (1, (1, 0)),
    (2, (0, 0)),
    (None, ...),
    (None, 4),
])
def test_accumulation_axiswise_get_value_valid_at_path(axis, data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda quib: np.cumsum(quib, axis=axis), data, path_to_get_value_at)

@pytest.mark.parametrize('indices_to_get_value_at, expected_a_calls, expected_b_calls', [
    (0, 1, 1),
    (1, 2, 1),
    (2, 2, 2),
    (3, 2, 2),
])
def test_accumulation_axiswise_get_value_valid_at_path_with_list_arg(indices_to_get_value_at,
                                                                     expected_a_calls, expected_b_calls):
    mock_func_a = mock.Mock(return_value=2)
    a = q(mock_func_a)
    mock_func_b = mock.Mock(return_value=3)
    b = q(mock_func_b)
    b = np.cumsum([1, a, b, 4])

    b.get_value_valid_at_path([PathComponent(indices_to_get_value_at)])
    assert mock_func_a.call_count == expected_a_calls
    assert mock_func_b.call_count == expected_b_calls
