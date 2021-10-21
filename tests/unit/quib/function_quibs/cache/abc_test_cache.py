from abc import ABC, abstractmethod

import pytest

from pyquibbler.quib.function_quibs.cache.shallow_cache import CacheStatus


class ABCTestCache(ABC):

    cls = NotImplemented
    result = NotImplemented

    @pytest.fixture()
    def cache(self):
        return self.cls.create_from_result(self.result)

    def test_matches_result_of_same_value(self, cache):
        assert cache.matches_result(self.result)

    def test_cache_starts_invalid(self, cache):
        uncached_paths = cache.get_uncached_paths([])

        assert uncached_paths == [[]]

    def test_cache_set_valid_makes_uncached_paths_empty(self, cache):
        cache.set_valid_value_at_path([], self.result)
        uncached_paths = cache.get_uncached_paths([])

        assert len(uncached_paths) == 0

    def test_cache_set_invalid_makes_uncached_paths_return_all(self, cache):
        cache.set_valid_value_at_path([], self.result)
        cache.set_invalid_at_path([])

        uncached_paths = cache.get_uncached_paths([])

        assert uncached_paths == [[]]

    def test_cache_get_value_when_valid(self, cache):
        cache.set_valid_value_at_path([], self.result)

        assert cache.get_value() == self.result

    def test_cache_get_cache_status_when_valid(self, cache):
        cache.set_valid_value_at_path([], self.result)

        assert cache.get_cache_status() == CacheStatus.ALL_VALID

    def test_cache_get_cache_status_when_invalid_at_start(self, cache):
        assert cache.get_cache_status() == CacheStatus.ALL_INVALID

    def test_cache_get_cache_status_when_invalid_after_valid(self, cache):
        cache.set_valid_value_at_path([], self.result)
        cache.set_invalid_at_path([])

        assert cache.get_cache_status() == CacheStatus.ALL_INVALID


class ABCTestIndexableCache(ABCTestCache):

    unsupported_type_result = NotImplemented
    empty_result = NotImplemented

    def test_cache_does_not_match_result_of_unsupported_type(self, cache):
        assert not cache.matches_result(self.unsupported_type_result)

    def test_cache_set_invalid_on_empty_result(self):
        cache = self.cls.create_from_result(self.empty_result)

        assert cache.get_cache_status() == CacheStatus.ALL_INVALID

    @abstractmethod
    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache):
        pass

    @abstractmethod
    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache):
        pass

    @abstractmethod
    def test_cache_get_cache_status_on_partial(self, cache):
        pass
