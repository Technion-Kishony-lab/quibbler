from unittest import mock

import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import IndexableCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest, SetValidTestCase, \
    SetInvalidTestCase


@pytest.mark.parametrize("result", [
    (1, 2, 3),
    [1, 2, 3],
])
class TestIndexableCache(IndexableCacheTest):

    cls = IndexableCache
    empty_result = []
    unsupported_type_result = {1, 2, 3}

    set_valid_test_cases = [
        SetValidTestCase(
            name="validate single index",
            valid_components=[0],
            valid_value=mock.Mock(),
            uncached_path_components=[],
        ),
        SetValidTestCase(
            name="validate slice",
            valid_components=[slice(1, None, None)],
            valid_value=[mock.Mock(), mock.Mock()],
            uncached_path_components=[],
        ),
        SetValidTestCase(
            name="validate all, get uncached paths at single index",
            valid_components=[],
            valid_value=[1, 2, 3],
            uncached_path_components=[1],
        ),
        SetValidTestCase(
            name="validate at single index, get uncached paths at same single index",
            valid_components=[1],
            valid_value=1,
            uncached_path_components=[1],
        ),
        SetValidTestCase(
            name="validate at single index, get uncached paths at same single index",
            valid_components=[1],
            valid_value=1,
            uncached_path_components=[1],
        ),
        SetValidTestCase(
            name="validate at slice, get uncached paths at slice",
            valid_components=[slice(1, 3, None)],
            valid_value=[mock.Mock, mock.Mock()],
            uncached_path_components=[slice(None, 2)],
        ),
        SetValidTestCase(
            name="validate at slice, get uncached paths at full slice",
            valid_components=[slice(1, 2, None)],
            valid_value=[mock.Mock()],
            uncached_path_components=[slice(None)],
        )
    ]

    set_invalid_test_cases = [
        SetInvalidTestCase(
            name="invalidate at single index",
            invalid_components=[1],
            uncached_path_components=[],
        ),
        SetInvalidTestCase(
            name="invalidate at slice without step",
            invalid_components=[slice(1, 3, None)],
            uncached_path_components=[],
        ),
        SetInvalidTestCase(
            name="invalidate at slice with only end",
            invalid_components=[slice(None, 2, None)],
            uncached_path_components=[],
        ),
        SetInvalidTestCase(
            name="invalidate at slice with start,step,end",
            invalid_components=[slice(0, 3, 2)],
            uncached_path_components=[],
        ),
        SetInvalidTestCase(
            name="invalidate at slice with end and step",
            invalid_components=[slice(None, 3, 2)],
            uncached_path_components=[],
        ),
        SetInvalidTestCase(
            name="invalidate at slice with start and step",
            invalid_components=[slice(0, None, 2)],
            uncached_path_components=[],
        )
    ]

    def get_values_from_result(self, result):
        return result if isinstance(result, list) else [result]

    def get_result_with_all_values_set_to_value(self, result, value):
        return [value for _ in result]

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        if len(path) == 0:
            return [value for _ in obj]

        working_indices = path[0].component
        if isinstance(working_indices, slice):
            length_to_broadcast = len(obj[working_indices])
            obj[working_indices] = [value for _ in range(length_to_broadcast)]
        else:
            obj[working_indices] = value
        return obj

    def test_list_cache_does_not_match_result_of_list_type_and_different_length(self, cache):
        assert not cache.matches_result([1, 2, 3, 4])

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(indexed_cls=list, component=slice(1, None, None))], [10, 10])
    
        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_list_cache_get_cache_status_when_completely_invalid_piece_by_piece(self, cache):
        cache.set_valid_value_at_path([], [10, 10])
    
        cache.set_invalid_at_path([PathComponent(component=0, indexed_cls=list)])
        cache.set_invalid_at_path([PathComponent(component=1, indexed_cls=list)])
    
        assert cache.get_cache_status() == CacheStatus.ALL_INVALID

    def test_cache_set_valid_makes_uncached_paths_empty(self, result, cache):
        cache.set_valid_value_at_path([], result)
        uncached_paths = cache.get_uncached_paths([])

        assert len(uncached_paths) == 0
    
    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, set_valid_test_case: SetValidTestCase):
        super(TestIndexableCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, result, set_valid_test_case)
        
    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result, set_invalid_test_case: SetInvalidTestCase):
        super(TestIndexableCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result, set_invalid_test_case)