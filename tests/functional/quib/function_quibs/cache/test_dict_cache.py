from unittest import mock

import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow import DictCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest


class TestDictCache(IndexableCacheTest):

    cls = DictCache

    unsupported_type_result = [1, 2, 3]

    paths = [
        [],
        ["a"],
        ["b"]
    ]

    @pytest.fixture()
    def result(self):
        return {"a": 1, "b": 2, "c": 3}

    def get_result_with_all_values_set_to_value(self, result, value):
        return {
            k: value
            for k in result
        }

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        if len(path) == 0:
            return {
                k: value
                for k in obj
            }
        working = path[0].component
        obj[working] = value
        return obj

    def get_values_from_result(self, result):
        if isinstance(result, dict):
            return list(result.values())
        return [result]

    def test_dict_cache_does_not_match_result_of_dict_type_and_different_keys(self, cache):
        assert not cache.matches_result({"a": 1})

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(indexed_cls=dict, component="a")], mock.Mock())

        assert cache.get_cache_status() == CacheStatus.PARTIAL

    @pytest.mark.parametrize("valid_value", [
        1,
        [1, 2, 3],
    ])
    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, valid_components,
                                                              uncached_path_components, valid_value):
        super(TestDictCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache, result, valid_components,
                                                                                       uncached_path_components,
                                                                                       valid_value)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self,  cache, result, invalid_components,
                                                              uncached_path_components):
        super(TestDictCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result,
                                                                                         invalid_components,
                                                                                         uncached_path_components)

    def set_completely_invalid(self, result, cache):
        for k in result:
            cache.set_invalid_at_path([PathComponent(component=k, indexed_cls=dict)])
