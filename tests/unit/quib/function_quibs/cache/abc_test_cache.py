from abc import ABC

import pytest


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

