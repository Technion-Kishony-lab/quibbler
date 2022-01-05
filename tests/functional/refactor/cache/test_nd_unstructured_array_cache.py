import numpy as np
import pytest

from pyquibbler.refactor.path import PathComponent
from pyquibbler.refactor.path.data_accessing import deep_assign_data_in_path
from pyquibbler.refactor.cache.cache import CacheStatus
from pyquibbler.refactor.cache.shallow.nd_cache import NdUnstructuredArrayCache
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest


class TestNdUnstructuredArrayCache(IndexableCacheTest):
    cls = NdUnstructuredArrayCache

    paths = [
        [([0, 0], [0, 1])],
        [slice(0)],
        [slice(0, 2, None)],
        [slice(None, 1, 2)],
        [(0, 1)],
        []
    ]

    unsupported_type_result = [1, 2, 3]

    @pytest.fixture
    def result(self):
        return np.array([[1, 2, 3], [4, 5, 6]])

    @pytest.fixture
    def valid_value(self):
        return 1

    def get_values_from_result(self, result):
        return np.ravel(result)

    def get_result_with_all_values_set_to_value(self, result, value):
        result[:] = value
        return result

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        if len(path) == 0:
            obj[:] = value
        else:
            obj = deep_assign_data_in_path(obj, path, value)
        return obj

    def test_nd_cache_does_not_match_nd_array_of_different_shape(self, cache):
        assert not cache.matches_result(np.arange(6).reshape((3, 2)))

    def test_nd_cache_does_not_match_nd_array_of_different_dtype(self, cache):
        assert not cache.matches_result(np.full((2, 3), "hello mike"))

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(component=(1, 1), indexed_cls=np.ndarray)], 5)

        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, valid_components,
                                                            uncached_path_components, valid_value):
        super(TestNdUnstructuredArrayCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, result,
                                                                                            valid_components, uncached_path_components,
                                                                                                      valid_value)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result, invalid_components,
                                                              uncached_path_components):
        super(TestNdUnstructuredArrayCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result,
                                                                                                 invalid_components,
                                                                                                 uncached_path_components)

    def set_completely_invalid(self, result, cache):
        cache.set_invalid_at_path([PathComponent(indexed_cls=np.ndarray, component=True)])

