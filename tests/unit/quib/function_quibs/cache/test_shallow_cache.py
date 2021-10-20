from unittest import mock

import pytest

from pyquibbler.quib.function_quibs.cache import ShallowCache
from pyquibbler.quib.function_quibs.cache.shallow_cache import PathCannotHaveComponentsException


@pytest.fixture
def shallow_cache() -> ShallowCache:
    return ShallowCache.create_from_result(1)


def test_shallow_cache_matches_all(shallow_cache):
    assert shallow_cache.matches_result(tuple())


def test_shallow_cache_starts_invalid(shallow_cache):
    uncached_paths = shallow_cache.get_uncached_paths([])

    assert uncached_paths == [[]]


def test_shallow_cache_set_valid_makes_uncached_paths_empty(shallow_cache):
    shallow_cache.set_valid_value_at_path([], 1)
    uncached_paths = shallow_cache.get_uncached_paths([])

    assert len(uncached_paths) == 0


def test_shallow_cache_set_invalid_makes_uncached_paths_return_all(shallow_cache):
    shallow_cache.set_valid_value_at_path([], 1)
    shallow_cache.set_invalid_at_path([])

    uncached_paths = shallow_cache.get_uncached_paths([])

    assert uncached_paths == [[]]


def test_shallow_cache_does_not_allow_specifying_paths_in_invalidate(shallow_cache):
    with pytest.raises(PathCannotHaveComponentsException):
        shallow_cache.set_invalid_at_path([mock.Mock()])


def test_shallow_cache_does_not_allow_specifying_paths_in_set_valid(shallow_cache):
    with pytest.raises(PathCannotHaveComponentsException):
        shallow_cache.set_valid_value_at_path([mock.Mock()], 1)
