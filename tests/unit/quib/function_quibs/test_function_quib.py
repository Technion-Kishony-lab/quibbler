import numpy as np
from pytest import fixture

from pyquibbler import iquib
from pyquibbler.quib import FunctionQuib
from pyquibbler.quib.assignment import Assignment, IndicesAssignment


class ExampleFunctionQuib(FunctionQuib):
    def _invalidate(self):
        pass

    def _get_inner_value(self):
        return self._call_func()


@fixture
def function_wrapper(function_mock):
    return ExampleFunctionQuib.create_wrapper(function_mock)


def test_create_wrapper_with_regular_args(function_wrapper, function_mock):
    args = (1, {})
    kwargs = {'a': 5, 'b': 'hello'}
    function_wrapper(*args, **kwargs)

    function_mock.assert_called_once_with(*args, **kwargs)


def test_create_wrapper_with_quib_args(function_wrapper, function_mock, function_mock_return_val):
    quib_val1 = 'ayy'
    quib_val2 = 'yo'
    function_quib = function_wrapper(iquib(quib_val1), a=iquib(quib_val2))

    assert isinstance(function_quib, ExampleFunctionQuib)
    function_mock.assert_not_called()
    assert function_quib.get_value() == function_mock_return_val
    function_mock.assert_called_once_with(quib_val1, a=quib_val2)


def test_cant_mutate_function_quib_args_after_creation(function_wrapper, function_mock):
    args = [[], iquib('cool')]
    kwargs = dict(a=[])
    function_quib = function_wrapper(*args, **kwargs)
    args[0].append(1)
    args.append(1)
    kwargs['b'] = 1
    kwargs['a'].append(1)
    function_quib.get_value()

    function_mock.assert_called_once_with([], 'cool', a=[])


def test_func_get_value_returns_inner_value(function_wrapper, function_mock_return_val):
    assert function_wrapper(iquib(1)).get_value() == function_mock_return_val


def test_assign_with_unknown_function_overrides(function_wrapper, function_mock_return_val):
    q = function_wrapper(iquib(np.array([1])))
    new_value = 420
    index = 2
    expected_value = np.array(function_mock_return_val)
    expected_value[index] = new_value

    q.assign(IndicesAssignment(value=new_value, indices=index))

    assert np.array_equal(q.get_value(), expected_value)


def test_quib_ancestors(function_wrapper):
    great_grandfather = iquib(1)
    grandparent = function_wrapper(great_grandfather)
    parent = function_wrapper(grandparent)
    me = function_wrapper(parent)

    assert me.ancestors == {great_grandfather, parent, grandparent}
