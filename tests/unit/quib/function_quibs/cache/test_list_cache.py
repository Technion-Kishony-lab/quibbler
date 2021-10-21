from unittest import mock

import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import ListShallowCache
from pyquibbler.quib.function_quibs.cache.shallow_cache import CacheStatus
from tests.unit.quib.function_quibs.cache.abc_test_cache import ABCTestCache, ABCTestIndexableCache


@pytest.fixture
def list_cache():
    return ListShallowCache.create_from_result([1, 2, 3])


def assert_uncached_paths_popped_out_falses_in_list(uncached_paths, lst):
    # todo: add comment
    if any([len(path) == 0 for path in uncached_paths]):
        return all([o is False for o in lst])

    for path in uncached_paths:
        assert len(path) == 1
        component = path[0]
        assert lst[component.component] is False
        lst[component.component] = True

    assert all([o is True for o in lst])


class TestListCache(ABCTestIndexableCache):

    cls = ListShallowCache
    result = [1, 2, 3]
    empty_result = []
    unsupported_type_result = {1, 2, 3}

    def test_list_cache_does_not_match_result_of_list_type_and_different_length(self, cache):
        assert not cache.matches_result([1, 2, 3, 4])

    @pytest.mark.parametrize("component,expected_valids", [
        (1, [True, False, True]),
        (slice(1, 3, None), [True, False, False]),
        (slice(None, 2, None), [False, False, True]),
        (slice(0, 3, 2), [False, True, False]),
        (slice(None, 3, 2), [False, True, False]),
        (slice(0, None, 2), [False, True, False]),
    ])
    def test_cache_set_invalid_partial(self, cache, component, expected_valids):
        cache.set_valid_value_at_path([], [2, 3, 4])
        cache.set_invalid_at_path([PathComponent(indexed_cls=list, component=component)])
        uncached_paths = cache.get_uncached_paths([])

        assert_uncached_paths_popped_out_falses_in_list(uncached_paths, expected_valids)

    @pytest.mark.parametrize("component,value,expected_valids", [
        (0, mock.Mock(), [True, False, False]),
        (slice(1, None, None), [mock.Mock(), mock.Mock()], [False, True, True]),
    ])
    def test_cache_set_valid_partial(self, cache, component, value, expected_valids):
        cache.set_valid_value_at_path([PathComponent(indexed_cls=list, component=component)], value)
        uncached_paths = cache.get_uncached_paths([])
    
        assert_uncached_paths_popped_out_falses_in_list(uncached_paths, expected_valids)

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(indexed_cls=list, component=slice(1, None, None))], [10, 10])
    
        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_list_cache_get_cache_status_when_completely_invalid_piece_by_piece(self, cache):
        cache.set_valid_value_at_path([], [10, 10])
    
        cache.set_invalid_at_path([PathComponent(component=0, indexed_cls=list)])
        cache.set_invalid_at_path([PathComponent(component=1, indexed_cls=list)])
    
        assert cache.get_cache_status() == CacheStatus.ALL_INVALID
