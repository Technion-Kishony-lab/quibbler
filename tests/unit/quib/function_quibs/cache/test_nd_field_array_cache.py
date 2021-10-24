import numpy as np
import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import get_sub_data_from_object_in_path, deep_assign_data_with_paths
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.quib.function_quibs.cache.shallow.nd_cache import NdFieldArrayShallowCache
from tests.unit.quib.function_quibs.cache.cache_test import IndexableCacheTest, SetValidTestCase, SetInvalidTestCase


class TestNdFieldArrayCache(IndexableCacheTest):

    cls = NdFieldArrayShallowCache
    dtype = [("name", np.str_, 20), ("age", np.int_)]
    boolean_dtype = [("name", np.bool_), ("age", np.bool_)]
    result = np.array([[("Maor", 24), ("Yossi", 15), ("Danahellilililili", 32)]], dtype=dtype)

    unsupported_type_result = [1, 2, 3]
    empty_result = np.array([], dtype=dtype)
    set_valid_test_cases = [
        SetValidTestCase(
            name="set single field, get all uncached",
            valid_components=["name"],
            valid_value="Jony",
            uncached_path_components=[],
            expected_value=np.array([[(False, True), (False, True), (False, True)]], dtype=boolean_dtype)
        ),
        SetValidTestCase(
            name="set single field, get same field uncached",
            valid_components=["name"],
            valid_value="Jony",
            uncached_path_components=["name"],
            expected_value=np.array([[(False, False), (False, False), (False, False)]], dtype=boolean_dtype)
        ),
        SetValidTestCase(
            name="set single field, get indices uncached",
            valid_components=["name"],
            valid_value="Jony",
            uncached_path_components=[(0, 0)],
            expected_value=np.array([[(False, True), (False, False), (False, False)]], dtype=boolean_dtype)
        ),
        SetValidTestCase(
            name="set indices, get all uncached",
            valid_components=[(0, 0)],
            valid_value="1",
            uncached_path_components=[],
            expected_value=np.array([[(False, False), (True, True), (True, True)]], dtype=boolean_dtype)
        ),
        SetValidTestCase(
            name="set indices, get field uncached",
            valid_components=[(0, 0)],
            valid_value="1",
            uncached_path_components=["name"],
            expected_value=np.array([[(False, False), (True, False), (True, False)]], dtype=boolean_dtype)
        ),
        SetValidTestCase(
            name="set indices, get field uncached",
            valid_components=[(0, 0)],
            valid_value="1",
            uncached_path_components=["name"],
            expected_value=np.array([[(False, False), (True, False), (True, False)]], dtype=boolean_dtype)
        )
    ]
    set_invalid_test_cases = [
        SetInvalidTestCase(
            name="set indices",
            invalid_components=[(0, 0)],
            uncached_path_components=[],
            expected_value=np.array([[(True, True), (False, False), (False, False)]], dtype=boolean_dtype)
        ),
        SetInvalidTestCase(
            name="set field",
            invalid_components=["name"],
            uncached_path_components=[],
            expected_value=np.array([[(True, False), (True, False), (True, False)]], dtype=boolean_dtype)
        ),
        SetInvalidTestCase(
            name="set indices, get field",
            invalid_components=[(0, 0)],
            uncached_path_components=["name"],
            expected_value=np.array([[(True, False), (False, False), (False, False)]], dtype=boolean_dtype)
        ),
        SetInvalidTestCase(
            name="set field, get indices",
            invalid_components=["age"],
            uncached_path_components=[(0, 0)],
            expected_value=np.array([[(False, True), (False, False), (False, False)]], dtype=boolean_dtype)
        )
    ]

    def assert_uncached_paths_match_expected_value(self, uncached_paths, expected_value):
        expected_value_arr = expected_value[:]
        for path in uncached_paths:
            assert np.all(get_sub_data_from_object_in_path(expected_value_arr, path))
            deep_assign_data_with_paths(expected_value_arr, path, False)
        assert not any(np.any(expected_value_arr[field]) for field in expected_value.dtype.names)

    @pytest.mark.parametrize("component", [
        (0, 1),
        "age"
    ])
    def test_cache_get_cache_status_on_partial(self, cache, component):
        cache.set_valid_value_at_path([PathComponent(component=component, indexed_cls=np.ndarray)], 5)

        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, set_valid_test_case: SetValidTestCase):
        super(TestNdFieldArrayCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, set_valid_test_case)
    
    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, set_invalid_test_case: SetInvalidTestCase):
        super(TestNdFieldArrayCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, set_invalid_test_case)