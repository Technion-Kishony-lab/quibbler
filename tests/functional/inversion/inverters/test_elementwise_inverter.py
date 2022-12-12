import operator

import numpy as np
import pytest
from typing import Iterable

from pyquibbler.path_translation.types import Source
from tests.functional.inversion.inverters.utils import inverse


@pytest.mark.parametrize("func,func_args,indices,value,quib_arg_index,expected_value", [
    (np.add, (Source(np.array([2, 2, 2])), np.array([5, 5, 5])), 0, 9, 0, np.array([4, 2, 2])),
    (np.add, (Source(np.array([[1, 2, 3], [4, 5, 6]])), np.array([5, 5, 5])), ([1], [2]), 100, 0, np.array([[1, 2, 3], [4, 5, 95]])),
    (np.add, (Source(np.array([5, 5, 5])), np.array([[1, 2, 3]])), ([0], [0]), 100, 0, np.array([99, 5, 5])),
    (np.subtract, (Source(np.array([5, 5, 5])), np.array([1, 1, 1])), ([0],), 0, 0, np.array([1, 5, 5])),
    (np.subtract, (np.array([10, 10, 10]), Source(np.array([1, 1, 1]))),  ([0],), 0, 1, np.array([10, 1, 1])),
    (np.subtract, (np.array([10, 10, 10]), Source(np.array([1, 1, 1]))),  ([0],), 3, 1, np.array([7, 1, 1])),
    (np.multiply, (Source(np.array([1, 1, 1])), np.array([10, 10, 10])), ([0],), 100, 0, np.array([10, 1, 1])),
    (np.divide, (Source(np.array([20, 20, 20])), np.array([5, 5, 5])), ([0],), 5, 0, np.array([25, 20, 20])),
    (np.divide, (np.array([20, 20, 20]), Source(np.array([5, 5, 5]))), ([0],), 5, 1, np.array([4, 5, 5])),
    (np.power, (Source(10), 2), None, 10_000, 0, 100),
    (np.power, (10, Source(1)), None, 100, 1, 2),
    (np.add, (Source(np.array([2])), np.array([5, 5, 5])), 0, 12, 0, np.array([7])),
    (np.add, (Source(2), np.array([5, 5, 5])), 0, 12, 0, 7),
    (np.add, (Source(2), np.array([5, 5, 5])), [False, True, False], 100, 0, 95),
    (np.arctan2, (3, Source(2.)), None, np.pi / 4, 1, 3),
    (np.arctan2, (Source(2.), 3), None, np.pi / 4, 0, 3),
], ids=[
    "add: simple",
    "add: multiple dimensions",
    "add: result with different shape than quib",
    "subtract: first arg is quib",
    "subtract: second arg is quib",
    "subtract: second arg is quib, non-zero",
    "multiply",
    "divide: first arg is quib",
    "divide: second arg is quib",
    "power: first arg is quib",
    "power: second arg is quib",
    "add: 1-size broadcasting to vector",
    "add: scalar broadcasting to vector",
    "add: scalar broadcasting to vector with boolean indexing",
    "arctan2: first agr",
    "arctan2: second agr",
])
def test_inverse_elementwise_two_arguments(func, func_args, indices, value, quib_arg_index, expected_value):
    sources_to_results, _ = inverse(func, indices=indices, value=value, args=func_args, empty_path=indices is None)

    value = sources_to_results[func_args[quib_arg_index]]
    if isinstance(expected_value, Iterable):
        assert np.allclose(value, expected_value)
    else:
        assert np.allclose(value, expected_value)
        assert np.shape(value) == np.shape(expected_value)


@pytest.mark.parametrize("func,func_args,value,quib_arg_index,expected_value", [
    (operator.add, (Source(2), 5), 10, 0, 5),
    (operator.sub, (100, Source(20)), 70, 1, 30),
])
def test_inverse_operator_two_arguments(func, func_args, value, quib_arg_index, expected_value):
    sources_to_results, _ = inverse(func, indices=None, value=value, args=func_args, empty_path=True)

    value = sources_to_results[func_args[quib_arg_index]]
    if isinstance(expected_value, Iterable):
        assert np.array_equal(value, expected_value)
    else:
        assert value == expected_value
        assert np.shape(value) == np.shape(expected_value)


@pytest.mark.parametrize("func,func_arg,indices,value,expected_value", [
    (np.abs, Source(10), None, 15, 15),
    (np.abs, Source(-10), None, 15, -15),
    (np.square, Source(10), None, 81, 9),
    (np.square, Source(-10), None, 81, -9),
    (np.square, Source(np.array([-3, 3, -4, 4])), slice(None, None, None), 81, np.array([-9, 9, -9, 9])),
    (np.square, Source(np.array([-3, 3, -4, 4])), slice(None, None, None), [81, 81, 81, 81], np.array([-9, 9, -9, 9])),
    (np.square, Source(np.array([-3, 3, -4, 4])), slice(None, -1, None), [81, 81, 81], np.array([-9, 9, -9, 4])),
    (np.square, Source(np.array([-3, 3, -4, 4])), slice(None, 3, None), [81, 81, 81], np.array([-9, 9, -9, 4])),
    (np.square, Source(np.array([-3, 3, -4, 4])), 2, 81, np.array([-3, 3, -9, 4])),
    (np.square, Source(np.array([-3, 3, -4, 4])), [0, 1, 2, 3], [81, 81, 81, 81], np.array([-9, 9, -9, 9])),
    (np.square, Source(np.array([-3, 3, -4, 4])), [0, 1, 2, 3], 81, np.array([-9, 9, -9, 9])),
    (np.negative, Source(1.8), None, 3,  -3),
    (np.sin, Source(6.), None, 0, 2*np.pi),
    (np.cos, Source(6.), None, 1, 2*np.pi),
    (np.tan, Source(6.), None, 0, 2 * np.pi),
], ids=[
    "abs: positive",
    "abs: negative",
    "square: scalar, positive",
    "square: scalar, negative",
    "square: array[:] = scalar",
    "square: array[:] = array",
    "square: array[:-1] = array",
    "square: array[:3] = array",
    "square: array[2] = scalar",
    "square: array[[0,1,2,3]] = array",
    "square: array[[0,1,2,3]] = scalar",
    "negative: scalar",
    "sin: scalar",
    "cos: scalar",
    "tan: scalar",
])
def test_inverse_elementwise_single_argument(func, func_arg, indices, value, expected_value):
    sources_to_results, _ = inverse(func, indices=indices, value=value, args=(func_arg,), empty_path=indices is None)

    value = sources_to_results[func_arg]
    if isinstance(expected_value, Iterable):
        assert np.array_equal(value, expected_value)
    else:
        assert value == expected_value
