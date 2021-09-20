from pytest import fixture

from pyquibbler import iquib
from pyquibbler.quib import FunctionQuib


class ExampleFunctionQuib(FunctionQuib):
    def _invalidate(self):
        pass

    def get_value(self):
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
    assert function_quib.get_value() is function_mock_return_val
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
