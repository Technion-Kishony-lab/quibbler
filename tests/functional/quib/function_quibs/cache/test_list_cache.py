from unittest import mock

import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import ListCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest, SetValidTestCase, \
    SetInvalidTestCase




class TestListCache(IndexableCacheTest):

    cls = ListCache
    result = [1, 2, 3]
    empty_result = []
    unsupported_type_result = {1, 2, 3}

    set_valid_test_cases = [
        SetValidTestCase(
            name="validate single index",
            valid_components=[0],
            valid_value=mock.Mock(),
            uncached_path_components=[],
            expected_value=[True, False, False]
        ),
        SetValidTestCase(
            name="validate slice",
            valid_components=[slice(1, None, None)],
            valid_value=[mock.Mock(), mock.Mock()],
            uncached_path_components=[],
            expected_value=[False, True, True]
        ),
        SetValidTestCase(
            name="validate all, get uncached paths at single index",
            valid_components=[],
            valid_value=[1, 2, 3],
            uncached_path_components=[1],
            expected_value=[]
        ),
        SetValidTestCase(
            name="validate at single index, get uncached paths at same single index",
            valid_components=[1],
            valid_value=1,
            uncached_path_components=[1],
            expected_value=[]
        ),
        SetValidTestCase(
            name="validate at single index, get uncached paths at same single index",
            valid_components=[1],
            valid_value=1,
            uncached_path_components=[1],
            expected_value=[]
        ),
        SetValidTestCase(
            name="validate at slice, get uncached paths at slice",
            valid_components=[slice(1, 3, None)],
            valid_value=[mock.Mock, mock.Mock()],
            uncached_path_components=[slice(None, 2)],
            expected_value=[False, True, True]
        ),
        SetValidTestCase(
            name="validate at slice, get uncached paths at full slice",
            valid_components=[slice(1, 2, None)],
            valid_value=[mock.Mock()],
            uncached_path_components=[slice(None)],
            expected_value=[False, True, False]
        )
    ]

    set_invalid_test_cases = [
        SetInvalidTestCase(
            name="invalidate at single index",
            invalid_components=[1],
            uncached_path_components=[],
            expected_value=[True, False, True]
        ),
        SetInvalidTestCase(
            name="invalidate at slice without step",
            invalid_components=[slice(1, 3, None)],
            uncached_path_components=[],
            expected_value=[True, False, False]
        ),
        SetInvalidTestCase(
            name="invalidate at slice with only end",
            invalid_components=[slice(None, 2, None)],
            uncached_path_components=[],
            expected_value=[False, False, True]
        ),
        SetInvalidTestCase(
            name="invalidate at slice with start,step,end",
            invalid_components=[slice(0, 3, 2)],
            uncached_path_components=[],
            expected_value=[False, True, False]
        ),
        SetInvalidTestCase(
            name="invalidate at slice with end and step",
            invalid_components=[slice(None, 3, 2)],
            uncached_path_components=[],
            expected_value=[False, True, False]
        ),
        SetInvalidTestCase(
            name="invalidate at slice with start and step",
            invalid_components=[slice(0, None, 2)],
            uncached_path_components=[],
            expected_value=[False, True, False]
        )
    ]

    def assert_uncached_paths_match_expected_value(self, uncached_paths, expected_value):
        valid_mask = expected_value[:]
        for path in uncached_paths:
            assert len(path) == 1
            component = path[0]
            assert valid_mask[component.component] is False
            valid_mask[component.component] = True

        assert all([o is True for o in valid_mask])

    def test_list_cache_does_not_match_result_of_list_type_and_different_length(self, cache):
        assert not cache.matches_result([1, 2, 3, 4])

    # We have this here to allow easy running from pycharm
    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, set_invalid_test_case: SetInvalidTestCase):
        super(TestListCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, set_invalid_test_case)

    # We have this here to allow easy running from pycharm
    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, set_valid_test_case: SetValidTestCase):
        super(TestListCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, set_valid_test_case)

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(indexed_cls=list, component=slice(1, None, None))], [10, 10])
    
        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_list_cache_get_cache_status_when_completely_invalid_piece_by_piece(self, cache):
        cache.set_valid_value_at_path([], [10, 10])
    
        cache.set_invalid_at_path([PathComponent(component=0, indexed_cls=list)])
        cache.set_invalid_at_path([PathComponent(component=1, indexed_cls=list)])
    
        assert cache.get_cache_status() == CacheStatus.ALL_INVALID

    def test_cache_set_valid_makes_uncached_paths_empty(self, cache):
        cache.set_valid_value_at_path([], self.result)
        uncached_paths = cache.get_uncached_paths([])

        assert len(uncached_paths) == 0
