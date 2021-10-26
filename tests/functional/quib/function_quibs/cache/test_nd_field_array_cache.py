import operator

import numpy as np
import pytest
from numpy.lib.recfunctions import structured_to_unstructured

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import get_sub_data_from_object_in_path, deep_assign_data_with_paths
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache import NdFieldArrayShallowCache
from pyquibbler.quib.utils import deep_copy_without_quibs_or_artists
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest

arr = np.array([[("Maor", 24), ("Yossi", 15), ("Danahellilililili", 32)]], dtype=[("name", np.str_, 20), ("age", np.int_)])


@pytest.mark.parametrize("result", [
    arr,
])
class TestNdFieldArrayCache(IndexableCacheTest):

    cls = NdFieldArrayShallowCache
    dtype = [("name", np.str_, 20), ("age", np.int_)]
    boolean_dtype = [("name", np.bool_), ("age", np.bool_)]

    unsupported_type_result = [1, 2, 3]
    empty_result = np.array([], dtype=dtype)

    def get_values_from_result(self, result):
        if isinstance(result, (np.ndarray, np.void)) and result.dtype.names is not None:
            result = structured_to_unstructured(result)
        return np.ravel(result)

    def get_result_with_all_values_set_to_value(self, result, value):
        result[:] = value
        return result

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        if len(path) == 0:
            obj[:] = value
        else:
            obj = deep_assign_data_with_paths(obj, path, value)
        return obj

    @pytest.mark.parametrize("component", [
        (0, 1),
        "age"
    ])
    def test_cache_get_cache_status_on_partial(self, cache, component):
        cache.set_valid_value_at_path([PathComponent(component=component, indexed_cls=np.ndarray)], 5)

        assert cache.get_cache_status() == CacheStatus.PARTIAL

    @pytest.mark.parametrize("valid_components", [
        ["name"],
        [(0, 0)]
    ])
    @pytest.mark.parametrize("uncached_path_components", [
        [(0, 0)],
        [],
        ["name"]
    ])
    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, valid_components,
                                                              uncached_path_components):
        super(TestNdFieldArrayCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, result,
                                                                                               valid_components,
                                                                                               uncached_path_components,
                                                                                               "1")

    @pytest.mark.parametrize("invalid_components", [
        [(0, 0)],
        [0],
        ["name"],
        []
    ])
    @pytest.mark.parametrize("uncached_path_components", [
        [],
        ["name"],
        [(0, 0)],
        [(0, 1)]
    ])
    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result, invalid_components,
                                                              uncached_path_components):
        super(TestNdFieldArrayCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result,
                                                                                              invalid_components,
                                                                                                 uncached_path_components)