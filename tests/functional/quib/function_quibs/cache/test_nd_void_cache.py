import numpy as np
import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache.nd_void_cache import NdVoidCache
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest


class TestNdVoidCache(IndexableCacheTest):
    cls = NdVoidCache
    empty_result = np.array([()], dtype=[])[0]

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
        obj = deep_assign_data_with_paths(obj, path, value)
        return obj

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(component=0, indexed_cls=np.void)], 5)

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