from unittest import mock

import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import DictShallowCache
from pyquibbler.quib.function_quibs.cache.shallow_cache import CacheStatus
from tests.unit.quib.function_quibs.cache.cache_test import IndexableCacheTest, SetValidTestCase, \
    SetInvalidTestCase


class TestDictCache(IndexableCacheTest):

    cls = DictShallowCache
    result = {"a": 1, "b": 2, "c": 3}
    unsupported_type_result = [1, 2, 3]
    empty_result = {}

    set_valid_test_cases = [
        SetValidTestCase(
            name="validate key, request all uncached",
            valid_components=["a"],
            valid_value=mock.Mock(),
            uncached_path_components=[],
            expected_value=["b", "c"]
        ),
        SetValidTestCase(
            name="validate key, request single uncached",
            valid_components=["a"],
            valid_value=mock.Mock(),
            uncached_path_components=["b"],
            expected_value=["b"]
        ),
        SetValidTestCase(
            name="validate key, request same key uncached",
            valid_components=["a"],
            valid_value=mock.Mock(),
            uncached_path_components=["a"],
            expected_value=[]
        )
    ]

    set_invalid_test_cases = [
        SetInvalidTestCase(
            name="invalidate key, request same key uncached",
            invalid_components=["a"],
            uncached_path_components=["a"],
            expected_value=["a"]
        ),
        SetInvalidTestCase(
            name="invalidate key, request different key uncached",
            invalid_components=["a"],
            uncached_path_components=["b"],
            expected_value=[]
        )
    ]

    def assert_uncached_paths_match_expected_value(self, uncached_paths, expected_value):
        keys_to_pop = set(expected_value)
        for path in uncached_paths:
            assert len(path) == 1
            inner_component = path[0].component
            assert inner_component in keys_to_pop, f"The key {inner_component} was in the paths but was not expected"
            keys_to_pop.remove(inner_component)

        assert len(keys_to_pop) == 0, f"The keys {keys_to_pop} were expected but not in the paths"

    def test_dict_cache_does_not_match_result_of_dict_type_and_different_keys(self, cache):
        assert not cache.matches_result({"a": 1})

    # We have this here to allow easy running from pycharm
    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache,
                                                              set_invalid_test_case: SetInvalidTestCase):
        super(TestDictCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache,
                                                                                         set_invalid_test_case)

    # We have this here to allow easy running from pycharm
    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, set_valid_test_case: SetValidTestCase):
        super(TestDictCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, set_valid_test_case)

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(indexed_cls=dict, component="a")], mock.Mock())

        assert cache.get_cache_status() == CacheStatus.PARTIAL
