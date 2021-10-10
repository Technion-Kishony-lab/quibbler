import numpy as np
import pytest
from collections import Iterable
from operator import __pow__

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib, FunctionQuib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.reverse_assignment import reverse_function_quib
from pyquibbler.quib.assignment.reverse_assignment.elementwise_reverser import CommonAncestorBetweenArgumentsException


def reverse(function_quib: FunctionQuib, value, paths):
    assignment = Assignment(value, paths)
    reversals = reverse_function_quib(function_quib=function_quib, assignment=assignment)
    for reversal in reversals:
        reversal.apply()


@pytest.mark.parametrize("function_quib,indices,value,quib_arg_index,expected_value", [
    (DefaultFunctionQuib.create(func=np.add,
                                func_args=(iquib(np.array([2, 2, 2])),
                                           np.array([5, 5, 5]))),
     0, 10, 0, np.array([5, 2, 2])
     ),
    (DefaultFunctionQuib.create(func=np.add,
                                func_args=(iquib(np.array([[1, 2, 3], [4, 5, 6]])),
                                           np.array([5, 5, 5]))),
     ([1], [2]), 100, 0, np.array([[1, 2, 3], [4, 5, 95]])
     ),
    (DefaultFunctionQuib.create(func=np.add,
                                func_args=(iquib(np.array([5, 5, 5])),
                                           np.array([[1, 2, 3]]))),
     ([0], [0]), 100, 0, np.array([99, 5, 5])
     ),
    (DefaultFunctionQuib.create(func=np.subtract,
                                func_args=(iquib(np.array([5, 5, 5])),
                                           np.array([1, 1, 1]))),
     ([0]), 0, 0, np.array([1, 5, 5])
     ),
    (DefaultFunctionQuib.create(func=np.subtract,
                                func_args=(
                                        np.array([10, 10, 10]),
                                        iquib(np.array([1, 1, 1])),
                                )),
     ([0]), 0, 1, np.array([10, 1, 1])
     ),
    (DefaultFunctionQuib.create(func=np.multiply,
                                func_args=(iquib(np.array([1, 1, 1])),
                                           np.array([10, 10, 10]))),
     ([0]), 100, 0, np.array([10, 1, 1])
     ),
    (DefaultFunctionQuib.create(func=np.divide,
                                func_args=(iquib(np.array([20, 20, 20])),
                                           np.array([5, 5, 5]))),
     ([0]), 5, 0, np.array([25, 20, 20])
     ),
    (DefaultFunctionQuib.create(func=np.divide,
                                func_args=(np.array([20, 20, 20]),
                                           iquib(np.array([5, 5, 5])))),
     ([0]), 5, 1, np.array([4, 5, 5]),
     ),
    (DefaultFunctionQuib.create(func=__pow__,
                                func_args=(iquib(10), 2)), ..., 10_000, 0, 100),
    (DefaultFunctionQuib.create(func=__pow__,
                                func_args=(10, iquib(1))), ..., 100, 1, 2)

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
    "power: second arg is quib"])
def test_reverse_elementwise(function_quib: FunctionQuib, indices, value, quib_arg_index, expected_value):
    reverse(function_quib, value, [indices])

    value = function_quib.args[quib_arg_index].get_value()
    if isinstance(expected_value, Iterable):
        assert np.array_equal(value, expected_value)
    else:
        assert value == expected_value


def test_reverse_elementwise_operator():
    q = iquib(np.array([5, 5, 5]))
    function_quib: FunctionQuib = q + 3

    reverse(function_quib, 7, [0])

    assert np.array_equal(q.get_value(), [4, 5, 5])


def test_reverse_elementwise_on_int():
    q = iquib(5)
    function_quib: FunctionQuib = q + 3

    reverse(function_quib, 7, paths=[...])

    assert q.get_value() == 4


@pytest.mark.regression
def test_quib_raises_exception_when_reversing_with_common_parent_in_multiple_args():
    x = iquib(5)
    y = x + 2
    z = x + 3
    function_quib: FunctionQuib = y + z

    with pytest.raises(CommonAncestorBetweenArgumentsException):
        reverse(function_quib, 20, [...])


@pytest.mark.regression
def test_add_second_argument_is_quib():
    quib = iquib(np.array(9))
    sum_ = 3 + quib

    reverse(sum_, 10, [...])

    assert np.array_equal(quib.get_value(), np.array(7))
