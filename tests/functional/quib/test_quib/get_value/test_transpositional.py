import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.path import PathComponent
from tests.functional.quib.test_quib.get_value.utils import check_get_value_valid_at_path


def test_can_getitem_on_object_without_diverged_cache():
    """
    If the function doesn't have a diverged cache it should request full validity from its parents,
    so it won't try to update the cache in a specific path component
    """
    obj = type('TypeACacheIsNotImplementedFor', (), dict(__getitem__=lambda self, item: item))()
    quib = iquib([obj])
    quib[0][0].get_value()


@pytest.mark.parametrize('data', [np.arange(24).reshape((2, 3, 4))])
@pytest.mark.parametrize('indices_to_get_value_at', [-1, 0, (1, 1), (2, 1, 3), [True, False, False], (0, ...)])
def test_transpositional_get_value(data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(np.rot90, data, path_to_get_value_at)


@pytest.mark.parametrize('data', [np.array([[('a', 23, 1), ('b', 24, 10), ('c', 25, 100)]],
                                           dtype=[('name', '|S21'), ('age', 'i8'), ('random', 'i4')])])
@pytest.mark.parametrize('indices_to_get_value_at', [
    (0,), (slice(0, 2)), 'name', slice(None), slice(None, 2)
])
def test_transpositional_get_value_with_fields(data, indices_to_get_value_at):
    path_to_get_value_at = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda x: x[0], data, path_to_get_value_at)


@pytest.mark.regression
@pytest.mark.parametrize('direction', [-1, 1])
@pytest.mark.parametrize('concat_with_quib', [True, False])
@pytest.mark.parametrize('indices_to_get_value_at', [0, 1, 2, -1])
@pytest.mark.parametrize('to_concat', [[0, 1],  # It's important for the regression that one of the elements here is 0
                                       [0., 1.]])  # It's important for the regression that array is not int
def test_concatenate_get_value_valid_at_path(direction, concat_with_quib, indices_to_get_value_at, to_concat):

    if concat_with_quib:
        to_concat = iquib(to_concat)
    path = [PathComponent(np.ndarray, indices_to_get_value_at)]
    check_get_value_valid_at_path(lambda q: np.concatenate((q, to_concat)[::direction]), np.array([0, 1]), path)


def filter_out_none_calls(mock_calls):
    return [
        mock_call
        for mock_call in mock_calls
        if mock_call.args[0] is not None
    ]


@pytest.mark.regression
def test_transpositional_concatenate_does_diverge(create_mock_quib):
    first = create_mock_quib((1, 3), ([[1, 2, 3]]))
    second = create_mock_quib((1, 3), ([[1, 2, 3]]))

    quib = np.concatenate((first, second))
    quib[1].get_value()

    assert len(filter_out_none_calls(first.get_value_valid_at_path.mock_calls)) == 0
    assert len(filter_out_none_calls(second.get_value_valid_at_path.mock_calls)) == 1


@pytest.mark.regression
def test_transpositional_get_value_minors(create_quib_with_return_value):
    first = create_quib_with_return_value([1, 2])
    second = np.array([0, 1, first])

    assert np.array_equal(second.get_value(), np.array([0, 1, [1, 2]], dtype=object))


@pytest.mark.regression
def test_transpositional_get_value_minors_2(create_quib_with_return_value):
    a = iquib(np.array([1, 2, 3, 4]))
    b = np.repeat([a], 3, 0)
    assert np.array_equal(b.get_value(), np.repeat([a.get_value()], 3, 0))
