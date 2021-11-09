import operator

import numpy as np
import pytest
from numpy.lib.recfunctions import structured_to_unstructured

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import get_sub_data_from_object_in_path, deep_assign_data_with_paths
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache import NdFieldArrayShallowCache
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest


class TestNdFieldArrayCache(IndexableCacheTest):

    cls = NdFieldArrayShallowCache
    dtype = [("name", np.str_, 20), ("age", np.int_)]
    boolean_dtype = [("name", np.bool_), ("age", np.bool_)]

    unsupported_type_result = [1, 2, 3]

    paths = [
        [],
        ["name"],
        [(0, 0)],
        [(0, 1)],
        [slice(0, None, None)],
        [slice(None)],
        [slice(None, 2, None)],
        ["age"]
    ]

    @pytest.fixture()
    def result(self):
        return np.array([[("Maor", 24), ("Yossi", 15), ("Danahellilililili", 32)]], dtype=self.dtype)

    @pytest.fixture()
    def valid_value(self):
        return "1"

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

    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, valid_components,
                                                              uncached_path_components, valid_value):
        super(TestNdFieldArrayCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, result,
                                                                                               valid_components,
                                                                                               uncached_path_components,
                                                                                               valid_value)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result, invalid_components,
                                                              uncached_path_components):
        super(TestNdFieldArrayCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result,
                                                                                              invalid_components,
                                                                                                 uncached_path_components)

    def set_completely_invalid(self, result, cache):
        cache.set_invalid_at_path([PathComponent(indexed_cls=np.ndarray, component=True)])
