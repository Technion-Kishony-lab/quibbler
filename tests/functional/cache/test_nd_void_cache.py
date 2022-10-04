import numpy as np
import pytest

from pyquibbler.path import PathComponent
from pyquibbler.cache.cache import CacheStatus
from pyquibbler.cache.shallow.nd_cache.nd_void_cache import NdVoidCache
from pyquibbler.path.data_accessing import deep_assign_data_in_path
from tests.functional.cache.cache_test import IndexableCacheTest


class TestNdVoidCache(IndexableCacheTest):
    cls = NdVoidCache

    paths = [
        [0],
        [1],
        ["name"],
        ["age"],
        []
    ]

    unsupported_type_result = np.array([1, 2, 3])

    @pytest.fixture
    def result(self):
        return np.array([("Maor", 22)], dtype=[("name", np.str_, 20), ("age", np.int_)])[0]

    @pytest.fixture
    def valid_value(self):
        return 1

    def get_values_from_result(self, result):
        return list(result) if isinstance(result, np.void) else [result]

    def get_result_with_all_values_set_to_value(self, result, value):
        for i in range(len(result)):
            result[i] = value
        return result

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        if len(path) == 0:
            return np.array([(value, value)], dtype=obj.dtype)[0]
        obj = deep_assign_data_in_path(obj, path, value)
        return obj

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(0)], 5)

        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, valid_components,
                                                            uncached_path_components, valid_value):
        super(TestNdVoidCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, result,
                                                                                            valid_components, uncached_path_components,
                                                                                                      valid_value)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result, invalid_components,
                                                              uncached_path_components):
        super(TestNdVoidCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result,
                                                                                                 invalid_components,
                                                                                                 uncached_path_components)

    def set_completely_invalid(self, result, cache):
        for name in result.dtype.names:
            cache.set_invalid_at_path([PathComponent(name)])
