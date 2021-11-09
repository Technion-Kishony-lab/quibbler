from typing import Optional, List, Any
from unittest import mock

import numpy as np
from unittest.mock import Mock

import pytest
from pytest import fixture, mark
from pyquibbler import iquib, CacheBehavior, q
from pyquibbler.env import PRETTY_REPR
from pyquibbler.input_validation_utils import InvalidArgumentException
from pyquibbler.quib import FunctionQuib, Assignment
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.function_quibs.function_quib import UnknownCacheBehaviorException

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
    q.set_allow_overriding(True)
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


@mark.regression
def test_function_quib_get_value_valid_at_path_with_data_source_kwarg():
    parent = MockQuib([[1]])
    quib = np.sum(a=parent, axis=1)
    quib.set_cache_behavior(CacheBehavior.OFF)
    with parent.collect_valid_paths() as paths:
        quib.get_value_valid_at_path([PathComponent(np.ndarray, 0)])

    assert len(paths) == 1
    assert [] not in paths


class InvalidatingFunctionQuib(FunctionQuib):

    def __init__(self, func, args, kwargs,
                 cache_behavior: Optional[CacheBehavior], data_source_quibs=None):
        super().__init__(func, args, kwargs, cache_behavior)
        self.data_source_quibs = data_source_quibs or []

    def _get_data_source_quibs(self):
        return self.data_source_quibs

    def _get_inner_value_valid_at_path(self, path: Optional[List[PathComponent]]) -> Any:
        return self._call_func(path)

    def _forward_translate_invalidation_path(self, invalidator_quib, path: List[PathComponent]) -> \
            List[List[PathComponent]]:
        return [path]


def test_function_quib_invalidates_all_when_invalidated_at_all_in_data_source(create_mock_quib):
    grandparent = InvalidatingFunctionQuib.create(func=mock.Mock())
    parent = InvalidatingFunctionQuib.create(func=mock.Mock(), func_args=(grandparent,),
                                             data_source_quibs=[grandparent])
    mock_quib = create_mock_quib()
    parent.add_child(mock_quib)

    grandparent.invalidate_and_redraw_at_path([])

    mock_quib._invalidate_quib_with_children_at_path.assert_called_with(parent, [])
    assert mock_quib._invalidate_quib_with_children_at_path.call_count == 1
    assert mock_quib.get_value_valid_at_path.call_count == 0


def test_function_quib_does_not_invalidate_all_when_invalidated_at_path_in_data_source(create_mock_quib):
    grandparent = InvalidatingFunctionQuib.create(func=mock.Mock())
    parent = InvalidatingFunctionQuib.create(func=mock.Mock(), func_args=(grandparent,),
                                             data_source_quibs=[grandparent])
    mock_quib = create_mock_quib()
    parent.add_child(mock_quib)
    path = [PathComponent(component=0, indexed_cls=list)]

    grandparent.invalidate_and_redraw_at_path(path)

    # Our default implementation for InvalidatingFunctionQuib is to forward by simply returning the path
    mock_quib._invalidate_quib_with_children_at_path.assert_called_with(parent, path)


def test_function_quib_does_invalidate_all_when_invalidated_partially_at_path_in_paramater(create_mock_quib):
    grandparent = InvalidatingFunctionQuib.create(func=mock.Mock())
    parent = InvalidatingFunctionQuib.create(func=mock.Mock(), func_args=(grandparent,))
    mock_quib = create_mock_quib()
    parent.add_child(mock_quib)
    path = [PathComponent(component=0, indexed_cls=list)]

    grandparent.invalidate_and_redraw_at_path(path)

    mock_quib._invalidate_quib_with_children_at_path.assert_called_with(parent, [])


def test_function_quib_does_invalidate_all_when_invalidated_all_at_path_in_parameter(create_mock_quib):
    grandparent = InvalidatingFunctionQuib.create(func=mock.Mock())
    parent = InvalidatingFunctionQuib.create(func=mock.Mock(), func_args=(grandparent,))
    mock_quib = create_mock_quib()
    parent.add_child(mock_quib)

    grandparent.invalidate_and_redraw_at_path([])

    mock_quib._invalidate_quib_with_children_at_path.assert_called_with(parent, [])


def test_function_quib_pretty_repr_without_name():
    a = iquib(1)
    b = iquib(2)

    assert q("".join, a, b).pretty_repr() == 'join(a, b)'


def test_function_quib_pretty_repr_with_name():
    a = iquib(1)
    b = iquib(2)
    c = q("".join, a, b)

    assert c.pretty_repr() == 'c = join(a, b)'


@mark.parametrize("statement", [
    "a[:]",
    "a[1:2:3]",
    "a[1::2]",
    "a[::2]",
    "a[:2]",
    "a[1:]"
])
def test_function_quib_pretty_repr_getitem_colon(statement):
    a = iquib(np.array([1, 2, 3]))
    b = eval(statement)

    assert b.pretty_repr() == statement


def test_function_quib_pretty_repr_getitem_ellipsis():
    a = iquib(np.array([1, 2, 3]))
    b = a[...]

    assert b.pretty_repr() == "b = a[...]"


def test_function_quib_pretty_repr_getitem_index():
    a = iquib(np.array([1, 2, 3]))
    b = a[1]

    assert b.pretty_repr() == "b = a[1]"


@fixture()
def a():
    a = iquib(1)
    return a


@fixture()
def b():
    b = iquib(1)
    return b


def test_function_quib_pretty_repr_math():
    a = iquib(1)
    b = iquib(2)
    c = a + b

    assert c.pretty_repr() == 'c = a + b'


@mark.parametrize("statement,expected", [
    ("a * b + b", "a * b + b"),
    ("a * (b + b)", "a * (b + b)"),
    ("(a * b) + b", "a * b + b"),
    ("a / (b * b) * a", "a / (b * b) * a"),
    ("a + a + a", "a + a + a"),
    ("a ** (a / (a + b))", "a ^ (a / (a + b))"),
    ("a - (a + a)", "a - (a + a)"),
    ("a / (a / a)", "a / (a / a)")
])
def test_function_quib_pretty_repr_math_holds_pemdas(a, b, statement, expected):
    with PRETTY_REPR.temporary_set(True):
        assert repr(eval(statement)) == expected


def test_function_quib_set_cache_behaviour_forces_correct_type(example_function_quib):
    with pytest.raises(InvalidArgumentException):
        example_function_quib.set_cache_behavior(1)


def test_function_quib_config(example_function_quib):
    example_function_quib.setp(cache_behavior='on')

    assert example_function_quib.get_cache_behavior() == CacheBehavior.ON


def test_function_quib_config_with_invalid_cache_behavior(example_function_quib):
    with pytest.raises(UnknownCacheBehaviorException):
        example_function_quib.setp(cache_behavior='ondfdd')
