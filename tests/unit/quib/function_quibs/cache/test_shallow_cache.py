from abc import ABC
from unittest import mock

import pytest

from pyquibbler.quib.function_quibs.cache import ShallowCache
from pyquibbler.quib.function_quibs.cache.shallow_cache import PathCannotHaveComponentsException
from tests.unit.quib.function_quibs.cache.abc_test_cache import ABCTestCache


class TestShallowCache(ABCTestCache):

    cls = ShallowCache
    result = 1

    def test_shallow_cache_matches_all(self, cache):
        assert cache.matches_result(object)

    def test_shallow_cache_does_not_allow_specifying_paths_in_invalidate(self, cache):
        with pytest.raises(PathCannotHaveComponentsException):
            cache.set_invalid_at_path([mock.Mock()])

    def test_shallow_cache_does_not_allow_specifying_paths_in_set_valid(self, cache):
        with pytest.raises(PathCannotHaveComponentsException):
            cache.set_valid_value_at_path([mock.Mock()], 1)
