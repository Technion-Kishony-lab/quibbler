import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib, FunctionQuib
from pyquibbler.quib.assignment.reverse_assignment import reverse_function_quib


@pytest.mark.parametrize("function_quib,indices,value,quib_arg_index,expected_value", [
    (DefaultFunctionQuib.create(func=np.add,
                                func_args=(iquib(np.array([2, 2, 2])), np.array([5, 5, 5]))),
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
     ([0]), 5, 1, np.array([4, 5, 5])
     ),

], ids=["add: simple",
        "add: multiple dimensions",
        "add: result with different shape than quib",
        "subtract: first arg is quib",
        "subtract: second arg is quib",
        "multiply",
        "divide: first arg is quib",
        "divide: second arg is quib"])
def test_reverse_elementwise(function_quib: FunctionQuib, indices, value, quib_arg_index, expected_value):

    reverse_function_quib(function_quib=function_quib,
                          indices=indices,
                          value=value)

    assert np.array_equal(function_quib.args[quib_arg_index].get_value(), expected_value)


def test_reverse_elementwise_operator():
    q = iquib(np.array([5, 5, 5]))
    function_quib = q + 3

    reverse_function_quib(function_quib=function_quib,
                          indices=0,
                          value=7)

    assert np.array_equal(q.get_value(), [4, 5, 5])


def test_reverse_elementwise_on_int():
    q = iquib(5)
    function_quib = q + 3

    reverse_function_quib(function_quib=function_quib,
                          indices=None,
                          value=7)

    assert q.get_value() == 4
