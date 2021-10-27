import numpy as np
from unittest.mock import Mock
from pytest import fixture, mark
from pyquibbler import iquib, CacheBehavior
from pyquibbler.quib import FunctionQuib, Assignment
from pyquibbler.quib.assignment.assignment import PathComponent

from ..utils import get_mock_with_repr, MockQuib


class ExampleFunctionQuib(FunctionQuib):
    def _invalidate(self):
        pass

    def _get_inner_value_valid_at_path(self, path):
        return self._call_func(None)


@fixture
def function_wrapper(function_mock):
    return ExampleFunctionQuib.create_wrapper(function_mock)


@fixture
def mock_overrides():
    return [Mock(), Mock()]


@fixture
def mock_options_tree_with_options(mock_overrides):
    options_tree_mock = Mock()
    options_tree_mock.__bool__ = Mock(return_value=True)
    options_tree_mock.choose_overrides = Mock(return_value=mock_overrides)
    return options_tree_mock


@fixture
def example_function_quib():
    return ExampleFunctionQuib.create(Mock())


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
    assert function_quib.get_value_valid_at_path([PathComponent(component=...,
                                                                indexed_cls=np.ndarray)]) \
           == function_mock_return_val
    function_mock.assert_called_once_with(quib_val1, a=quib_val2)


def test_cant_mutate_function_quib_args_after_creation(function_wrapper, function_mock):
    args = [[], iquib('cool')]
    kwargs = dict(a=[])
    function_quib = function_wrapper(*args, **kwargs)
    args[0].append(1)
    args.append(1)
    kwargs['b'] = 1
    kwargs['a'].append(1)
    function_quib.get_value_valid_at_path([PathComponent(component=..., indexed_cls=np.ndarray)])

    function_mock.assert_called_once_with([], 'cool', a=[])


def test_func_get_value_returns_inner_value(function_wrapper, function_mock_return_val):
    assert function_wrapper(iquib(1)).get_value() == function_mock_return_val


def test_assign_with_unknown_function_overrides(function_wrapper, function_mock_return_val):
    q = function_wrapper(iquib(np.array([1])))
    q.allow_overriding = True
    new_value = 420
    index = 2
    expected_value = np.array(function_mock_return_val)
    expected_value[index] = new_value

    q.assign(Assignment(value=new_value, path=[PathComponent(component=index, indexed_cls=q.get_type())]))

    assert np.array_equal(q.get_value(), expected_value)


def test_quib_ancestors(function_wrapper):
    great_grandparent = iquib(1)
    grandparent = function_wrapper(great_grandparent)
    parent = function_wrapper(grandparent)
    me = function_wrapper(parent)

    assert me.ancestors == {great_grandparent, parent, grandparent}


def test_parents():
    parent1 = iquib(1)
    grandparent = iquib(2)
    parent2 = ExampleFunctionQuib.create(Mock(), (grandparent,))
    fquib = ExampleFunctionQuib.create(Mock(), (0, parent1, 2), dict(a=parent2, b=3))

    assert fquib.parents == {parent1, parent2}


@mark.lazy(False)
def function_quib_create_calculates_when_not_lazy(function_mock):
    ExampleFunctionQuib.create(function_mock)

    function_mock.assert_called_once()


def test_pretty_repr():
    function_repr = 'woohoo'
    function = get_mock_with_repr(function_repr)
    parent = iquib('lolol')
    fquib = ExampleFunctionQuib.create(function, (parent,))

    string = fquib.pretty_repr()

    assert function_repr in string
    assert parent.get_value() in string


@mark.regression
def test_function_quib_get_value_valid_at_path_with_data_source_kwarg():
    parent = MockQuib([[1]])
    quib = np.sum(a=parent, axis=1)
    quib.set_cache_behavior(CacheBehavior.OFF)
    with parent.collect_valid_paths() as paths:
        quib.get_value_valid_at_path([PathComponent(np.ndarray, 0)])

    assert len(paths) == 1
    assert [] not in paths
