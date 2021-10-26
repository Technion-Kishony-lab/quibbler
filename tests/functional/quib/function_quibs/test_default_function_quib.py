from unittest import mock

import numpy as np
import pytest
from pytest import fixture, mark

from pyquibbler import iquib, CacheBehavior
from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus


@fixture
def quib_cached_result():
    return 'quib_cached_result'


@fixture
def parent_quib():
    return iquib([0])


@fixture
def default_function_quib(function_mock):
    fquib = DefaultFunctionQuib.create(function_mock, cache_behavior=CacheBehavior.ON)
    fquib.allow_overriding = True
    return fquib


@fixture
def quib_with_valid_cache(parent_quib, function_mock, quib_cached_result):
    quib = DefaultFunctionQuib(func=function_mock, args=(parent_quib,), kwargs={}, cache_behavior=CacheBehavior.ON,
                               is_cache_valid=True, cached_result=quib_cached_result)
    parent_quib.add_child(quib)
    return quib


def test_calculation_is_lazy(default_function_quib, function_mock):
    function_mock.assert_not_called()
    assert default_function_quib.cache_status == CacheStatus.ALL_INVALID


def test_no_caching_is_done_when_cache_is_off(function_mock, function_mock_return_val):
    function_quib = DefaultFunctionQuib.create(function_mock, cache_behavior=CacheBehavior.OFF)
    path_to_get_value = []

    assert function_quib.get_value_valid_at_path(path_to_get_value) == function_mock_return_val
    assert function_quib.cache_status == CacheStatus.ALL_INVALID
    assert function_quib.get_value_valid_at_path(path_to_get_value) == function_mock_return_val
    assert function_mock.call_count == 2


@mark.regression
def test_overrides_do_not_mutate_internal_cache(default_function_quib, function_mock_return_val):
    new_val = object()
    default_function_quib[0] = new_val
    default_function_quib.get_value()

    assert function_mock_return_val[0] is not new_val


def test_invalidation_invalidates_quib_when_needed():
    quib = iquib(np.array([[1, 2, 3]]))
    mock_func = mock.Mock()
    mock_func.return_value = 1
    function_quib = DefaultFunctionQuib.create(
        func=mock_func,
        func_args=(quib, 1)
    )
    mock_dependant_quib = DefaultFunctionQuib.create(
        func=mock_func,
        func_args=(function_quib,)
    )
    function_quib.invalidate_and_redraw_at_path(path=[PathComponent(indexed_cls=function_quib.get_type(),
                                                                    component=(0, 0))])

    assert mock_dependant_quib.cache_status == CacheStatus.ALL_INVALID


@pytest.mark.regression
def test_second_level_nested_argument_quib_is_replaced():
    a = iquib(np.arange(6).reshape(2, 3))

    # We are checking this doesn't raise an exception
    assert np.array_equal(a[1, iquib(1):1].get_value(), np.array([]))


def test_get_value_with_cache_requesting_all_valid_caches_result():
    mock_func = mock.Mock()
    mock_func.return_value = [1, 2, 3]
    quib = DefaultFunctionQuib.create(
        func=mock_func,
        func_args=tuple()
    )
    quib.get_value_valid_at_path([])
    # We want to make sure we don't call our mock_func anymore, so we save the number here
    current_call_count = mock_func.call_count

    result1 = quib.get_value_valid_at_path([PathComponent(indexed_cls=list, component=0)])
    result2 = quib.get_value_valid_at_path([PathComponent(indexed_cls=list, component=1)])
    result3 = quib.get_value_valid_at_path([PathComponent(indexed_cls=list, component=2)])

    assert mock_func.call_count == current_call_count
    assert result1 == result2 == result3 == [1, 2, 3]


def test_get_value_with_cache_with_changing_type():
    parent = iquib(1)
    mock_func = mock.Mock()
    mock_func.side_effect = [[1, 2, 3], {"a": 1}]
    quib = DefaultFunctionQuib.create(
        func=mock_func,
        func_args=(parent,)
    )

    quib.get_value_valid_at_path([PathComponent(indexed_cls=list, component=1)])
    parent.invalidate_and_redraw_at_path([])
    new_value = quib.get_value_valid_at_path([PathComponent(indexed_cls=dict, component="a")])

    assert new_value == {"a": 1}


def test_invalidate_before_cache_exists():
    parent = iquib(1)
    _ = DefaultFunctionQuib.create(
        func=mock.Mock(),
        func_args=(parent,)
    )

    # simply make sure we don't throw an exception
    parent.invalidate_and_redraw_at_path([])


@pytest.mark.regression
def test_default_function_quib_set_cache_resets_cache():
    mock_func = mock.Mock()
    mock_func.side_effect = [1, 2]
    quib = DefaultFunctionQuib.create(
        func=mock_func,
    )
    quib.get_value()

    quib.set_cache_behavior(CacheBehavior.OFF)
    result = quib.get_value()

    assert result == 2
