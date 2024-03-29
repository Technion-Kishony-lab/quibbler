from unittest import mock

import numpy as np
import pytest

from pyquibbler import iquib, q
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.quib import Quib
from pyquibbler.path.path_component import PathComponent
from tests.functional.quib.test_quib.get_value.utils import check_get_value_valid_at_path


def test_elementwise_function_quib_does_not_request_unneeded_indices_on_get_value(create_mock_quib):
    fake_quib = create_mock_quib()
    fake_quib.get_value_valid_at_path.return_value = np.array([1, 2])
    fake_quib.get_shape.return_value = (2,)
    b = np.add(fake_quib, 1)

    result = b.get_value_valid_at_path([PathComponent(1)])

    assert result[1] == 3
    calls_requesting_values = [c for c in fake_quib.get_value_valid_at_path.mock_calls if c.args != (None,)]
    assert len(calls_requesting_values) == 1
    second_call = calls_requesting_values[0]
    assert isinstance(second_call.args[0][0], PathComponent)
    component = second_call.args[0][0]
    assert bool(np.array([False, True])[component.component]) is True


def test_elementwise_function_quib_does_not_request_unneeded_indices_on_get_value_of_minor_sources():
    mock_func = mock.Mock(return_value=3)
    a = q(mock_func)
    b = np.exp2([1, 2, a, 4])

    mock_func.assert_not_called()

    b.get_value_valid_at_path([PathComponent(0)])
    assert mock_func.call_count == 1  # it was only called for get_shape()

    b.get_value_valid_at_path([PathComponent(1)])
    assert mock_func.call_count == 1  # it was only called for get_shape()

    b.get_value_valid_at_path([PathComponent(2)])
    assert mock_func.call_count == 2  # now it called for get_value()


@pytest.mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
@pytest.mark.parametrize('indices_to_get_value_at', [-1, 0, (1, 1), (1, 2, 3), [True, False], (0, ...)])
def test_elementwise_get_value(data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda x: np.add(x, 1), data, path_to_get_value_at)


@pytest.mark.regression
def test_elementwise_with_no_parents():
    # https://github.com/Technion-Kishony-lab/pyquibbler/issues/191
    assert create_quib(np.sin, args=(0,)).get_value() == 0


@pytest.mark.regression
def test_elementwise_on_scalar_quib_and_array():
    # https://github.com/Technion-Kishony-lab/pyquibbler/issues/178
    a = iquib(3)
    b = a + np.array([0, 1])
    b.get_value()


@pytest.mark.allow_array_with_dtype_object(True)
def test_object_array():
    a = iquib([1, 2])
    b = np.array(['nothing here', a], dtype=object)

    assert np.array_equal(b.get_value(), np.array(['nothing here', a.get_value()], dtype=object))


@pytest.mark.regression
def test_array_of_arrays():
    a_value = np.array([0, 1, 2])
    a = iquib(a_value)
    b = np.array([a, None], dtype=object)  # use None to force np.array avoiding collapse to single array
    b1 = b[0]
    assert np.array_equal(np.exp2(b1).get_value(), np.exp2(a_value))
