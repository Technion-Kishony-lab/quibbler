import numpy as np
import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import NdShallowCache
from pyquibbler.quib.function_quibs.cache.shallow_cache import CacheStatus


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


def assert_and_get_single_uncached_path_component(uncached_paths):
    assert len(uncached_paths) == 1
    uncached_path = uncached_paths[0]
    assert len(uncached_path) == 1
    component = uncached_path[0]
    return component


def test_nd_cache_set_valid_partial_returns_correct_paths(nd_array_cache):
    nd_array_cache.set_valid_value_at_path([PathComponent(component=(1, 1), indexed_cls=np.ndarray)],
                                           5)
    uncached_paths = nd_array_cache.get_uncached_paths([])

    component = assert_and_get_single_uncached_path_component(uncached_paths)
    assert np.all(np.array([[True, True, True], [True, False, True]])[component.component])


def test_nd_cache_cache_status_on_partial_validity(nd_array_cache):
    nd_array_cache.set_valid_value_at_path([PathComponent(component=(1, 1), indexed_cls=np.ndarray)], 5)

    assert nd_array_cache.get_cache_status() == CacheStatus.PARTIAL


def test_nd_cache_get_uncached_paths_on_partial_returns_partial(nd_array_cache):
    nd_array_cache.set_valid_value_at_path([PathComponent(component=(0, 1), indexed_cls=np.ndarray)], 5)

    uncached_paths = nd_array_cache.get_uncached_paths([PathComponent(component=([0, 0], [0, 1]),
                                                                      indexed_cls=np.ndarray)])

    component = assert_and_get_single_uncached_path_component(uncached_paths)
    assert np.all(np.array([[True, False, False], [False, False, False]])[component.component])


def test_nd_cache_invalidate_empty_nd():
    nd_shallow_cache = NdShallowCache.create_from_result(np.array([]))

    uncached_paths = nd_shallow_cache.get_uncached_paths([])

    assert len(uncached_paths) == 1

@pytest.fixture()
def nd_array_cache_with_field_array():
    dtype = [("name", np.str_, 20), ("age", np.int_, 64)]
    return NdShallowCache.create_from_result(
        np.array([("Maor", 24), ("Yossi", 15), ("Danahellilililili", 32)], dtype=dtype)
    )


def test_nd_cache_field_array_set_invalid_all(nd_array_cache_with_field_array):
    nd_array_cache_with_field_array.set_invalid_at_path([])

    paths = nd_array_cache_with_field_array.get_uncached_paths([])

    assert len(paths) == 2
    for i, component_name in enumerate(['name', 'age']):
        assert np.all(np.full((3,), True)[paths[i][1].component])


def test_nd_cache_field_array_set_valid_on_field(nd_array_cache_with_field_array):
    nd_array_cache_with_field_array.set_valid_value_at_path([PathComponent(component="name", indexed_cls=np.ndarray)],
                                                            5)
    paths = nd_array_cache_with_field_array.get_uncached_paths([])

    assert len(paths) == 1
    path = paths[0]
    assert len(path) == 2
    first_component = path[0]
    assert first_component.component == "age"
    second_component = path[1]
    assert np.all(np.logical_and(np.full((3,), True), second_component.component))


def test_nd_cache_field_array_set_valid_on_indices(nd_array_cache_with_field_array):
    nd_array_cache_with_field_array.set_valid_value_at_path([PathComponent(component=0, indexed_cls=np.ndarray)],
                                                            5)
    paths = nd_array_cache_with_field_array.get_uncached_paths([])

    assert len(paths) == 2
    for i, component_name in enumerate(['name', 'age']):
        path = paths[i]
        assert len(path) == 2
        assert path[0].component == component_name
        assert np.all(np.array([False, True, True])[path[1].component])

# todo: add more tests for returning partials
# todo: add test for get_value
