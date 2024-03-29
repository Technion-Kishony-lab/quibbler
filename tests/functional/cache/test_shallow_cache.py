from unittest import mock

import pytest

from pyquibbler.cache.holistic_cache import HolisticCache, PathCannotHaveComponentsException
from pyquibbler.path import PathComponent
from tests.functional.cache.cache_test import CacheTest


class TestShallowCache(CacheTest):

    cls = HolisticCache

    @pytest.fixture()
    def result(self):
        return 1

    def test_shallow_cache_matches_all(self, cache):
        assert cache.matches_result(object)

    def test_shallow_cache_does_not_allow_specifying_paths_in_invalidate(self, cache):
        with pytest.raises(PathCannotHaveComponentsException, match='.*'):
            cache.set_invalid_at_path([PathComponent(7)])

    def test_shallow_cache_does_not_allow_specifying_paths_in_set_valid(self, cache):
        with pytest.raises(PathCannotHaveComponentsException, match='.*'):
            cache.set_valid_value_at_path([PathComponent(7)], 1)
