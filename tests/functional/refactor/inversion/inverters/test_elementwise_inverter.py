from operator import __pow__

import numpy as np
import pytest
from typing import Iterable

from pyquibbler.refactor.translation.types import Source
from tests.functional.refactor.inversion.inverters.utils import inverse


@pytest.mark.parametrize("func,func_args,indices,value,quib_arg_index,expected_value", [
    (np.add, (Source(np.array([2, 2, 2])), np.array([5, 5, 5])), 0, 10, 0, np.array([5, 2, 2])),
    (np.add, (Source(np.array([[1, 2, 3], [4, 5, 6]])), np.array([5, 5, 5])), ([1], [2]), 100, 0, np.array([[1, 2, 3], [4, 5, 95]])),
    (np.add, (Source(np.array([5, 5, 5])), np.array([[1, 2, 3]])), ([0], [0]), 100, 0, np.array([99, 5, 5])),
    (np.subtract, (Source(np.array([5, 5, 5])), np.array([1, 1, 1])), ([0],), 0, 0, np.array([1, 5, 5])),
    (np.subtract, (np.array([10, 10, 10]), Source(np.array([1, 1, 1]))),  ([0],), 0, 1, np.array([10, 1, 1])),
    (np.multiply, (Source(np.array([1, 1, 1])), np.array([10, 10, 10])), ([0],), 100, 0, np.array([10, 1, 1])),
    (np.divide, (Source(np.array([20, 20, 20])), np.array([5, 5, 5])), ([0],), 5, 0, np.array([25, 20, 20])),
    (np.divide, (np.array([20, 20, 20]), Source(np.array([5, 5, 5]))), ([0],), 5, 1, np.array([4, 5, 5])),
    (np.power, (Source(10), 2), None, 10_000, 0, 100),
    (np.power, (10, Source(1)), None, 100, 1, 2),
], ids=[
    "add: simple",
    "add: multiple dimensions",
    "add: result with different shape than quib",
    "subtract: first arg is quib",
    "subtract: second arg is quib",
    "multiply",
    "divide: first arg is quib",
    "divide: second arg is quib",
    "power: first arg is quib",
    "power: second arg is quib",
])
def test_inverse_elementwise_two_arguments(func, func_args, indices, value, quib_arg_index, expected_value):
    sources_to_results = inverse(func, indices=indices, value=value, args=func_args, empty_path=indices is None)

    value = sources_to_results[func_args[quib_arg_index]]
    if isinstance(expected_value, Iterable):
        assert np.array_equal(value, expected_value)
    else:
        assert value == expected_value


@pytest.mark.parametrize("func,func_arg,indices,value,expected_value", [
    (np.abs, Source(10), None, 15, 15),
    (np.abs, Source(-10), None, 15, -15),
    (np.int, Source(1.8), None, 3,  3),
], ids=[
    "abs: positive",
    "abs: negative",
    "int: float-to-int",
])
def test_inverse_elementwise_single_argument(func, func_arg, indices, value, expected_value):
    sources_to_results = inverse(func, indices=indices, value=value, args=(func_arg,), empty_path=indices is None)

    value = sources_to_results[func_arg]
    if isinstance(expected_value, Iterable):
        assert np.array_equal(value, expected_value)
    else:
        assert value == expected_value
