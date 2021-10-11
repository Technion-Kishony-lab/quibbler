from operator import getitem
from unittest import mock

import numpy as np
from pytest import fixture, mark

from pyquibbler import iquib, CacheBehavior, Assignment
from pyquibbler.quib import DefaultFunctionQuib


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
    assert not default_function_quib.is_cache_valid


def test_calculation_enters_cache(default_function_quib, function_mock, function_mock_return_val):
    result = default_function_quib.get_value()

    assert result == function_mock_return_val
    assert default_function_quib.is_cache_valid
    function_mock.assert_called_once()


def test_calculation_not_redone_when_cache_valid(quib_with_valid_cache, function_mock, quib_cached_result):
    result = quib_with_valid_cache.get_value()
    function_mock.assert_not_called()

    assert result == quib_cached_result
    assert quib_with_valid_cache.is_cache_valid


def test_invalidation(parent_quib, quib_with_valid_cache, quib_cached_result, function_mock, function_mock_return_val):
    parent_quib[0] = 1
    assert not quib_with_valid_cache.is_cache_valid
    result = quib_with_valid_cache.get_value()

    assert result == function_mock_return_val
    function_mock.assert_called_once()


def test_no_caching_is_done_when_cache_is_off(function_mock, function_mock_return_val):
    function_quib = DefaultFunctionQuib.create(function_mock, cache_behavior=CacheBehavior.OFF)

    assert function_quib.get_value() == function_mock_return_val
    assert not function_quib.is_cache_valid
    assert function_quib.get_value() == function_mock_return_val
    assert function_mock.call_count == 2


@mark.regression
def test_overrides_do_not_mutate_internal_cache(default_function_quib, function_mock_return_val):
    new_val = object()
    default_function_quib[0] = new_val
    default_function_quib.get_value()

    assert function_mock_return_val[0] is not new_val


def test_invalidation_invalidates_quib_when_needed():
    quib = iquib(np.array([[1, 2, 3]]))
    function_quib = DefaultFunctionQuib.create(
        func=mock.Mock(),
        func_args=(quib, 1)
    )
    mock_dependant_quib = DefaultFunctionQuib.create(
        func=mock.Mock(),
        func_args=(function_quib,)
    )
    function_quib.invalidate_and_redraw(path=[(0, 0)])

    assert not mock_dependant_quib.is_cache_valid
