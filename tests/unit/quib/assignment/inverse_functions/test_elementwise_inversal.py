import numpy as np
import pytest
from typing import Iterable
from operator import __pow__

from pyquibbler import iquib
from pyquibbler.quib import ElementWiseFunctionQuib, FunctionQuib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.assignment.inverse_assignment.elementwise_inverter import CommonAncestorBetweenArgumentsException


def inverse(function_quib: FunctionQuib, value, path):
    assignment = Assignment(value, path)
    inversions = function_quib.get_inversions_for_assignment(assignment=assignment)
    for inversion in inversions:
        inversion.apply()


@pytest.mark.parametrize("function_quib,indices,value,quib_arg_index,expected_value", [
    (ElementWiseFunctionQuib.create(func=np.add,
                                func_args=(iquib(np.array([2, 2, 2])),
                                           np.array([5, 5, 5]))),
     0, 10, 0, np.array([5, 2, 2])
     ),
    (ElementWiseFunctionQuib.create(func=np.add,
                                func_args=(iquib(np.array([[1, 2, 3], [4, 5, 6]])),
                                           np.array([5, 5, 5]))),
     ([1], [2]), 100, 0, np.array([[1, 2, 3], [4, 5, 95]])
     ),
    (ElementWiseFunctionQuib.create(func=np.add,
                                func_args=(iquib(np.array([5, 5, 5])),
                                           np.array([[1, 2, 3]]))),
     ([0], [0]), 100, 0, np.array([99, 5, 5])
     ),
    (ElementWiseFunctionQuib.create(func=np.subtract,
                                func_args=(iquib(np.array([5, 5, 5])),
                                           np.array([1, 1, 1]))),
     ([0]), 0, 0, np.array([1, 5, 5])
     ),
    (ElementWiseFunctionQuib.create(func=np.subtract,
                                func_args=(
                                        np.array([10, 10, 10]),
                                        iquib(np.array([1, 1, 1])),
                                )),
     ([0]), 0, 1, np.array([10, 1, 1])
     ),
    (ElementWiseFunctionQuib.create(func=np.multiply,
                                func_args=(iquib(np.array([1, 1, 1])),
                                           np.array([10, 10, 10]))),
     ([0]), 100, 0, np.array([10, 1, 1])
     ),
    (ElementWiseFunctionQuib.create(func=np.divide,
                                func_args=(iquib(np.array([20, 20, 20])),
                                           np.array([5, 5, 5]))),
     ([0]), 5, 0, np.array([25, 20, 20])
     ),
    (ElementWiseFunctionQuib.create(func=np.divide,
                                func_args=(np.array([20, 20, 20]),
                                           iquib(np.array([5, 5, 5])))),
     ([0]), 5, 1, np.array([4, 5, 5]),
     ),
    (ElementWiseFunctionQuib.create(func=__pow__, func_args=(iquib(10), 2)), None, 10_000, 0, 100),
    (ElementWiseFunctionQuib.create(func=__pow__, func_args=(10, iquib(1))), None, 100, 1, 2)

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
def test_inverse_elementwise(function_quib: FunctionQuib, indices, value, quib_arg_index, expected_value):
    if indices is None:
        path = []
    else:
        path = [PathComponent(component=indices, indexed_cls=function_quib.get_type())]
    inverse(function_quib, value, path)

    value = function_quib.args[quib_arg_index].get_value()
    if isinstance(expected_value, Iterable):
        assert np.array_equal(value, expected_value)
    else:
        assert value == expected_value


def test_inverse_elementwise_operator():
    q = iquib(np.array([5, 5, 5]))
    function_quib: FunctionQuib = q + 3

    inverse(function_quib, 7, [PathComponent(component=0, indexed_cls=function_quib.get_type())])

    assert np.array_equal(q.get_value(), [4, 5, 5])


def test_inverse_elementwise_on_int():
    q = iquib(5)
    function_quib: FunctionQuib = q + 3

    inverse(function_quib, 7, path=[])

    assert q.get_value() == 4


def test_inverse_on_neg_operator():
    q = iquib(3)
    function_quib: FunctionQuib = -q

    inverse(function_quib, 7, path=[])

    assert q.get_value() == -7


@pytest.mark.regression
@pytest.mark.assignment_restrictions(True)
def test_quib_raises_exception_when_reversing_with_common_parent_in_multiple_args():
    x = iquib(5)
    y = x + 2
    z = x + 3
    function_quib: FunctionQuib = y + z

    with pytest.raises(CommonAncestorBetweenArgumentsException):
        inverse(function_quib, 20, [])


@pytest.mark.regression
def test_add_second_argument_is_quib():
    quib = iquib(np.array(9))
    sum_ = 3 + quib

    inverse(sum_, 10, [])

    assert np.array_equal(quib.get_value(), np.array(7))


@pytest.mark.regression
def test_elementwise_always_picks_first_quib():
    first_quib = iquib(1)
    second_quib = iquib(2)

    inverse(first_quib + second_quib, 5, [])
    assert first_quib.get_value() == 3

    inverse(second_quib + first_quib, 7, [])
    assert second_quib.get_value() == 4


def test_elementwise_with_deep_path():
    first_quib = iquib([[1, 2, 3]])
    sum_quib = ElementWiseFunctionQuib.create(func=np.add, func_args=(first_quib, 1))
    getitem_quib = sum_quib[0]

    inverse(getitem_quib, path=[PathComponent(component=0, indexed_cls=getitem_quib.get_type())], value=0)

    assert np.array_equal(first_quib.get_value(), [[-1, 2, 3]])


@pytest.mark.assignment_restrictions(False)
def test_elementwise_doesnt_raise_exception_when_assignment_restrictions_off():
    quib = iquib(100)
    fquib = quib - quib

    fquib.assign_value(50)

    assert fquib.get_value() == 0
