import numpy as np
import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import NdShallowCache


@pytest.fixture
def nd_array_cache() -> NdShallowCache:
    return NdShallowCache.create_from_result(np.array([[1, 2, 3], [4, 5, 6]]))


def test_nd_cache_matches_nd_array_of_same_shape(nd_array_cache):
    assert nd_array_cache.matches_result(np.arange(6).reshape((2, 3)))


def test_nd_cache_does_not_match_nd_array_of_different_shape(nd_array_cache):
    assert not nd_array_cache.matches_result(np.arange(6).reshape((3, 2)))


def test_nd_cache_does_not_match_different_type(nd_array_cache):
    assert not nd_array_cache.matches_result(23)


def test_nd_cache_does_not_match_nd_array_of_different_dtype(nd_array_cache):
    assert not nd_array_cache.matches_result(np.full((2, 3), "hello mike"))


def test_nd_cache_starts_invalid(nd_array_cache):
    uncached_paths = nd_array_cache.get_uncached_paths([])

    assert len(uncached_paths) == 1
    # we try not to check actual path as there could potentially be differnt ways to portray a path of everything
    # (all Trues, indexes of everything, a single True, etc)
    assert np.all(np.logical_and(np.full((2, 3), True), uncached_paths[0][0].component))


def test_nd_cache_set_valid_all_returns_no_uncached_paths(nd_array_cache):
    nd_array_cache.set_valid_value_at_path([], np.full((2, 3), 1))
    uncached_paths = nd_array_cache.get_uncached_paths([])

    assert len(uncached_paths) == 0


def test_nd_cache_set_valid_partial_returns_correct_paths(nd_array_cache):
    nd_array_cache.set_valid_value_at_path([PathComponent(component=(1, 1), indexed_cls=np.ndarray)],
                                           5)
    uncached_paths = nd_array_cache.get_uncached_paths([])

    assert len(uncached_paths) == 1
    uncached_path = uncached_paths[0]
    assert len(uncached_path) == 1
    component = uncached_path[0]
    assert np.all(np.array([[True, True, True], [True, False, True]])[component.component])


def test_nd_cache_set_valid_partial_returns_correct_paths(nd_array_cache):
    nd_array_cache.set_valid_value_at_path([PathComponent(component=(1, 1), indexed_cls=np.ndarray)],
                                           5)
    uncached_paths = nd_array_cache.get_uncached_paths([])

    assert len(uncached_paths) == 1
    uncached_path = uncached_paths[0]
    assert len(uncached_path) == 1
    component = uncached_path[0]
    assert np.all(np.array([[True, True, True], [True, False, True]])[component.component])


