from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
import pytest
from numpy.lib.recfunctions import structured_to_unstructured

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from pyquibbler.quib.utils import deep_copy_without_quibs_or_artists


class CacheTest(ABC):

    cls = NotImplemented

    @pytest.fixture()
    def cache(self, result):
        return self.cls.create_from_result(result)

    def test_matches_result_of_same_value(self, cache):
        assert cache.matches_result(cache.get_value())

    def test_cache_starts_invalid(self, cache):
        uncached_paths = cache.get_uncached_paths([])

        assert uncached_paths == [[]], f"{uncached_paths=}"

    def test_cache_set_valid_makes_uncached_paths_empty(self, cache, result):
        cache.set_valid_value_at_path([], result)
        uncached_paths = cache.get_uncached_paths([])

        assert len(uncached_paths) == 0

    def test_cache_set_invalid_all_makes_uncached_paths_return_all(self, cache, result):
        cache.set_valid_value_at_path([], result)
        cache.set_invalid_at_path([])

        uncached_paths = cache.get_uncached_paths([])

        assert uncached_paths == [[]]

    def test_cache_get_value_when_valid(self, cache, result):
        cache.set_valid_value_at_path([], result)

        if isinstance(result, np.ndarray):
            assert np.array_equal(cache.get_value(), result)
        else:
            assert cache.get_value() == result

    def test_cache_get_cache_status_when_valid(self, cache, result):
        cache.set_valid_value_at_path([], result)

        assert cache.get_cache_status() == CacheStatus.ALL_VALID

    def test_cache_get_cache_status_when_invalid_at_start(self, cache):
        assert cache.get_cache_status() == CacheStatus.ALL_INVALID

    def test_cache_get_cache_status_when_invalid_after_valid(self, cache, result):
        cache.set_valid_value_at_path([], result)
        cache.set_invalid_at_path([])

        assert cache.get_cache_status() == CacheStatus.ALL_INVALID


@dataclass
class SetValidTestCase:

    name: str
    valid_components: list
    valid_value: Any
    uncached_path_components: list


@dataclass
class SetInvalidTestCase:

    name: str
    invalid_components: list
    uncached_path_components: list


class IndexableCacheTest(CacheTest):

    unsupported_type_result = NotImplemented
    empty_result = NotImplemented
    set_valid_test_cases = NotImplemented
    set_invalid_test_cases = NotImplemented

    def __init_subclass__(cls, **kwargs):
        parametrized_valid = pytest.mark.parametrize("set_valid_test_case", cls.set_valid_test_cases)\
            (cls.test_cache_set_valid_partial_and_get_uncached_paths)
        cls.test_cache_set_valid_partial_and_get_uncached_paths = parametrized_valid

        parametrized_invalid = pytest.mark.parametrize("set_invalid_test_case", cls.set_invalid_test_cases) \
            (cls.test_cache_set_invalid_partial_and_get_uncached_paths)
        cls.test_cache_set_invalid_partial_and_get_uncached_paths = parametrized_invalid

    @abstractmethod
    def get_values_from_result(self, result):
        pass

    @abstractmethod
    def get_result_with_all_values_set_to_value(self, result, value):
        pass

    @abstractmethod
    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        pass

    def assert_uncached_paths_match_expected_value(self, result, path, uncached_paths, filter_path,
                                                   invert_starting_and_setting_point):
        invalid_value = 7070
        valid_value = 6969
        checked_invalid = 7171
        checking_result = deep_copy_without_quibs_or_artists(result)

        starting = invalid_value
        setting = valid_value

        if invert_starting_and_setting_point:
            starting = valid_value
            setting = invalid_value

        checking_result = self.get_result_with_all_values_set_to_value(checking_result, starting)
        checking_result = self.get_result_with_value_broadcasted_to_path(checking_result, path, setting)

        for path in uncached_paths:
            data = get_sub_data_from_object_in_path(checking_result, path)
            for x in np.nditer(data):
                assert str(x) == str(invalid_value)

            checking_result = self.get_result_with_value_broadcasted_to_path(checking_result, path, checked_invalid)

        items = get_sub_data_from_object_in_path(checking_result, filter_path)
        assert all(str(x) == str(checked_invalid) or str(x) == str(valid_value)
                   for x in self.get_values_from_result(items))

    def test_cache_does_not_match_result_of_unsupported_type(self, cache):
        assert not cache.matches_result(self.unsupported_type_result)

    def test_cache_set_invalid_on_empty_result(self, result):
        cache = self.cls.create_from_result(self.empty_result)

        assert cache.get_cache_status() == CacheStatus.ALL_INVALID

    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, set_valid_test_case: SetValidTestCase):
        valid_path = [PathComponent(component=v, indexed_cls=type(result))
                      for v in set_valid_test_case.valid_components]
        cache.set_valid_value_at_path(valid_path, set_valid_test_case.valid_value)

        uncached_path = [PathComponent(component=u, indexed_cls=type(result)) for u in
                                          set_valid_test_case.uncached_path_components]
        paths = cache.get_uncached_paths(uncached_path)

        self.assert_uncached_paths_match_expected_value(result, valid_path, paths, uncached_path, False)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result, set_invalid_test_case: SetInvalidTestCase):
        cache.set_valid_value_at_path([], deep_copy_without_quibs_or_artists(result))
        invalid_path = [PathComponent(component=v, indexed_cls=type(result))
                      for v in set_invalid_test_case.invalid_components]
        cache.set_invalid_at_path(invalid_path)
        filter_path = [PathComponent(component=u, indexed_cls=type(result)) for u in
                                          set_invalid_test_case.uncached_path_components]
        uncached_paths = cache.get_uncached_paths(filter_path)

        self.assert_uncached_paths_match_expected_value(result, invalid_path, uncached_paths,
                                                                filter_path, True)

    @abstractmethod
    def test_cache_get_cache_status_on_partial(self, cache):
        pass

