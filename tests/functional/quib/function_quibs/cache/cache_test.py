from abc import ABC, abstractmethod
from copy import copy
from dataclasses import dataclass
from typing import Any

import numpy as np
import pytest
from numpy.lib.recfunctions import structured_to_unstructured

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.utils import deep_assign_data_with_paths, get_sub_data_from_object_in_path
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus, CannotInvalidateEntireCacheException
from pyquibbler.quib.utils import deep_copy_without_quibs_or_artists


class CacheTest(ABC):

    cls = NotImplemented
    starting_valid_path = []

    @pytest.fixture()
    def cache(self, result):
        return self.cls.create_from_result(result, self.starting_valid_path)

    def test_matches_result_of_same_value(self, cache):
        assert cache.matches_result(cache.get_value())

    def test_cache_set_valid_makes_uncached_paths_empty(self, cache, result):
        cache.set_valid_value_at_path([], result)
        uncached_paths = cache.get_uncached_paths([])

        assert len(uncached_paths) == 0

    def test_cache_set_invalid_all_raises_exception(self, cache, result):
        cache.set_valid_value_at_path([], result)

        with pytest.raises(CannotInvalidateEntireCacheException):
            cache.set_invalid_at_path([])

    def test_cache_get_value_when_valid(self, cache, result):
        cache.set_valid_value_at_path([], result)

        if isinstance(result, np.ndarray):
            assert np.array_equal(cache.get_value(), result)
        else:
            assert cache.get_value() == result

    def test_cache_get_cache_status_when_valid(self, cache, result):
        cache.set_valid_value_at_path([], result)

        assert cache.get_cache_status() == CacheStatus.ALL_VALID


class IndexableCacheTest(CacheTest):

    starting_valid_path = []

    unsupported_type_result = NotImplemented
    empty_result = NotImplemented

    paths = NotImplemented

    def __init_subclass__(cls, **kwargs):
        parametrized_invalid = pytest.mark.parametrize("invalid_components", [p for p in cls.paths if p != []] ) \
            (cls.test_cache_set_invalid_partial_and_get_uncached_paths)
        parametrized_invalid = pytest.mark.parametrize("uncached_path_components", cls.paths)(parametrized_invalid)
        cls.test_cache_set_invalid_partial_and_get_uncached_paths = parametrized_invalid

        parametrized_valid = pytest.mark.parametrize("valid_components", cls.paths) \
            (cls.test_cache_set_valid_partial_and_get_uncached_paths)
        parametrized_valid = pytest.mark.parametrize("uncached_path_components", cls.paths)(parametrized_valid)
        cls.test_cache_set_valid_partial_and_get_uncached_paths = parametrized_valid

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
            for x in self.get_values_from_result(data):
                assert str(x) == str(invalid_value)

            checking_result = self.get_result_with_value_broadcasted_to_path(checking_result, path, checked_invalid)

        items = get_sub_data_from_object_in_path(checking_result, filter_path)
        assert all(str(x) == str(checked_invalid) or str(x) == str(valid_value)
                   for x in self.get_values_from_result(items))

    def test_cache_does_not_match_result_of_unsupported_type(self, cache):
        assert not cache.matches_result(self.unsupported_type_result)

    def test_cache_set_valid_partial_and_get_uncached_paths(self, result, valid_components,
                                                              uncached_path_components, valid_value):
        valid_path = [PathComponent(component=v, indexed_cls=type(result))
                      for v in valid_components]
        cache = self.cls.create_from_result(result, valid_path)

        result_with_valid_value = self.get_result_with_value_broadcasted_to_path(copy(result),
                                                                                 valid_path, valid_value)
        broadcasted_value = get_sub_data_from_object_in_path(result_with_valid_value, valid_path)

        cache.set_valid_value_at_path(valid_path, broadcasted_value)

        uncached_path = [PathComponent(component=u, indexed_cls=type(result)) for u in
                                          uncached_path_components]
        paths = cache.get_uncached_paths(uncached_path)

        self.assert_uncached_paths_match_expected_value(result, valid_path, paths, uncached_path, False)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self,  cache, result, invalid_components,
                                                              uncached_path_components):
        cache.set_valid_value_at_path([], deep_copy_without_quibs_or_artists(result))
        invalid_path = [PathComponent(component=v, indexed_cls=type(result))
                      for v in invalid_components]
        cache.set_invalid_at_path(invalid_path)
        filter_path = [PathComponent(component=u, indexed_cls=type(result)) for u in
                                          uncached_path_components]
        uncached_paths = cache.get_uncached_paths(filter_path)

        self.assert_uncached_paths_match_expected_value(result, invalid_path, uncached_paths,
                                                                filter_path, True)

    # @abstractmethod
    def test_cache_get_cache_status_when_invalid(self, cache):
        pass

    @abstractmethod
    def test_cache_get_cache_status_on_partial(self, cache):
        pass

