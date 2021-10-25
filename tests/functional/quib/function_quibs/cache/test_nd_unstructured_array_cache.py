import numpy as np
import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache import NdUnstructuredArrayCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest, SetValidTestCase, SetInvalidTestCase


class TestNdUnstructuredArrayCache(IndexableCacheTest):
    cls = NdUnstructuredArrayCache
    result = np.array([[1, 2, 3], [4, 5, 6]])

    unsupported_type_result = [1, 2, 3]
    empty_result = np.array([])
    set_valid_test_cases = [
        SetValidTestCase(
            name="set valid with index, get uncached without",
            uncached_path_components=[],
            valid_components=[(1, 1)],
            valid_value=5,
            expected_value=[[True, True, True], [True, False, True]]
        ),
        SetValidTestCase(
            name="set valid with fancy indexing, get uncached without",
            uncached_path_components=[([0, 0], [0, 1])],
            valid_components=[(0, 1)],
            valid_value=5,
            expected_value=[[True, False, False], [False, False, False]]
        ),
    ]
    set_invalid_test_cases = [
        SetInvalidTestCase(
            name="invalidate single, get all uncached",
            invalid_components=[(0, 1)],
            uncached_path_components=[],
            expected_value=[[False, True, False], [False, False, False]],
        ),
        SetInvalidTestCase(
            name="invalidate with index and slice, get all uncached",
            invalid_components=[(0, slice(0, 2))],
            uncached_path_components=[],
            expected_value=[[True, True, False], [False, False, False]],
        )
    ]

    def assert_uncached_paths_match_expected_value(self, uncached_paths, expected_value):
        assert len(uncached_paths) == 1
        component = uncached_paths[0][0].component
        expected_value_arr = np.array(expected_value)
        assert np.all(expected_value_arr[component])
        assert not np.any(expected_value_arr[np.logical_not(component)])

    def test_nd_cache_does_not_match_nd_array_of_different_shape(self, cache):
        assert not cache.matches_result(np.arange(6).reshape((3, 2)))

    def test_nd_cache_does_not_match_nd_array_of_different_dtype(self, cache):
        assert not cache.matches_result(np.full((2, 3), "hello mike"))
    
    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, set_valid_test_case: SetValidTestCase):
        super(TestNdUnstructuredArrayCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, set_valid_test_case)
    
    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, set_invalid_test_case: SetInvalidTestCase):
        super(TestNdUnstructuredArrayCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, set_invalid_test_case)

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(component=(1, 1), indexed_cls=np.ndarray)], 5)

        assert cache.get_cache_status() == CacheStatus.PARTIAL

