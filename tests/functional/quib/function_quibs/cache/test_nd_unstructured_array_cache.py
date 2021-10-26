import numpy as np
import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache import NdUnstructuredArrayCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest, SetValidTestCase, SetInvalidTestCase


class TestNdUnstructuredArrayCache(IndexableCacheTest):
    cls = NdUnstructuredArrayCache
    result = np.array([[1, 2, 3], [4, 5, 6]])

    @pytest.fixture
    def result(self):
        return np.array([[1, 2, 3], [4, 5, 6]])

    unsupported_type_result = [1, 2, 3]
    empty_result = np.array([])
    set_valid_test_cases = [
        SetValidTestCase(
            name="set valid with index, get uncached without",
            uncached_path_components=[],
            valid_components=[(1, 1)],
            valid_value=5,
        ),
        SetValidTestCase(
            name="set valid with fancy indexing, get uncached without",
            uncached_path_components=[([0, 0], [0, 1])],
            valid_components=[(0, 1)],
            valid_value=5,
        ),
    ]
    set_invalid_test_cases = [
        SetInvalidTestCase(
            name="invalidate single, get all uncached",
            invalid_components=[(0, 1)],
            uncached_path_components=[],
        ),
        SetInvalidTestCase(
            name="invalidate with index and slice, get all uncached",
            invalid_components=[(0, slice(0, 2))],
            uncached_path_components=[],
        )
    ]

    def get_values_from_result(self, result):
        return list(np.ravel(result))

    def get_result_with_all_values_set_to_value(self, result, value):
        result[:] = value
        return result

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        deep_assign_data_with_paths(obj, path, value)
        return obj

    def test_nd_cache_does_not_match_nd_array_of_different_shape(self, cache):
        assert not cache.matches_result(np.arange(6).reshape((3, 2)))

    def test_nd_cache_does_not_match_nd_array_of_different_dtype(self, cache):
        assert not cache.matches_result(np.full((2, 3), "hello mike"))

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(component=(1, 1), indexed_cls=np.ndarray)], 5)

        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, set_valid_test_case: SetValidTestCase):
        super(TestNdUnstructuredArrayCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, result,
                                                                                            set_valid_test_case)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result,
                                                              set_invalid_test_case: SetInvalidTestCase):
        super(TestNdUnstructuredArrayCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result,
                                                                                              set_invalid_test_case)