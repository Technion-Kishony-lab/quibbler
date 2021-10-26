from unittest import mock

import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache.shallow import DictCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest, SetValidTestCase, \
    SetInvalidTestCase


class TestDictCache(IndexableCacheTest):

    cls = DictCache

    @pytest.fixture()
    def result(self):
        return {"a": 1, "b": 2, "c": 3}

    unsupported_type_result = [1, 2, 3]
    empty_result = {}

    set_valid_test_cases = [
        SetValidTestCase(
            name="validate key, request all uncached",
            valid_components=["a"],
            valid_value=mock.Mock(),
            uncached_path_components=[],
        ),
        SetValidTestCase(
            name="validate key, request single uncached",
            valid_components=["a"],
            valid_value=mock.Mock(),
            uncached_path_components=["b"],
        ),
        SetValidTestCase(
            name="validate key, request same key uncached",
            valid_components=["a"],
            valid_value=mock.Mock(),
            uncached_path_components=["a"],
        )
    ]

    set_invalid_test_cases = [
        SetInvalidTestCase(
            name="invalidate key, request same key uncached",
            invalid_components=["a"],
            uncached_path_components=["a"],
        ),
        SetInvalidTestCase(
            name="invalidate key, request different key uncached",
            invalid_components=["a"],
            uncached_path_components=["b"],
        )
    ]

    def get_result_with_all_values_set_to_value(self, result, value):
        return {
            k: value
            for k in result
        }

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
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
