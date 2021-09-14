from pytest import fixture

from pyquibbler import iquib, CacheBehavior
from pyquibbler.quib import DefaultFunctionQuib


@fixture
def quib_cached_result():
    return object()


@fixture
def parent_quib():
    return iquib([0])


@fixture
def quib_with_valid_cache(parent_quib, function_mock, quib_cached_result):
    quib = DefaultFunctionQuib(set(), [], function_mock, (parent_quib,), {}, CacheBehavior.ON, True, quib_cached_result)
    parent_quib.add_child(quib)
    return quib


def test_calculation_is_lazy(function_mock):
    function_quib = DefaultFunctionQuib.create(function_mock, cache_behavior=CacheBehavior.ON)
    function_mock.assert_not_called()
    assert not function_quib.is_cache_valid


def test_calculation_enters_cache(function_mock, function_mock_return_val):
    function_quib = DefaultFunctionQuib.create(function_mock, cache_behavior=CacheBehavior.ON)
    result = function_quib.get_value()
    assert result is function_mock_return_val
    assert function_quib.is_cache_valid
    function_mock.assert_called_once()


def test_calculation_not_redone_when_cache_valid(quib_with_valid_cache, function_mock, quib_cached_result):
    result = quib_with_valid_cache.get_value()
    function_mock.assert_not_called()
    assert result is quib_cached_result
    assert quib_with_valid_cache.is_cache_valid


def test_invalidation(parent_quib, quib_with_valid_cache, quib_cached_result, function_mock, function_mock_return_val):
    parent_quib[0] = 1
    assert not quib_with_valid_cache.is_cache_valid
    result = quib_with_valid_cache.get_value()
    assert result is function_mock_return_val
    function_mock.assert_called_once()


def test_no_caching_is_done_when_cache_is_off(function_mock, function_mock_return_val):
    function_quib = DefaultFunctionQuib.create(function_mock, cache_behavior=CacheBehavior.OFF)
    assert function_quib.get_value() is function_mock_return_val
    assert not function_quib.is_cache_valid
    assert function_quib.get_value() is function_mock_return_val
    assert function_mock.call_count == 2
