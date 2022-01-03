from unittest import mock

import numpy as np
import pytest

from pyquibbler.refactor.quib.quib import Quib, PathComponent
from tests.functional.refactor.quib.test_quib.get_value.utils import check_get_value_valid_at_path


def test_elementwise_function_quib_does_not_request_unneeded_indices_on_get_value():
    fake_quib = mock.Mock(spec=Quib)
    fake_quib.get_value_valid_at_path.return_value = np.array([1, 2])
    fake_quib.get_shape.return_value = (2,)
    b = np.add(fake_quib, 1)

    result = b.get_value_valid_at_path([PathComponent(
        indexed_cls=np.ndarray,
        component=1
    )])

    assert result[1] == 3
    calls_requesting_values = [c for c in fake_quib.get_value_valid_at_path.mock_calls if c.args != (None,)]
    assert len(calls_requesting_values) == 1
    second_call = calls_requesting_values[0]
    assert isinstance(second_call.args[0][0], PathComponent)
    component = second_call.args[0][0]
    assert bool(np.array([False, True])[component.component]) is True


@pytest.mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
@pytest.mark.parametrize('indices_to_get_value_at', [-1, 0, (1, 1), (1, 2, 3), [True, False], (0, ...)])
def test_elementwise_get_value(data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda x: np.add(x, 1), data, path_to_get_value_at)
