import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import ListShallowCache


@pytest.fixture
def list_cache():
    return ListShallowCache.create_from_result([1, 2, 3])


def assert_uncached_paths_popped_out_falses_in_list(uncached_paths, lst):
    for path in uncached_paths:
        assert len(path) == 1
        component = path[0]
        assert lst[component.component] is False
        lst[component.component] = True

    assert all([o is True for o in lst])


def test_list_cache_matches_result_of_list_type_and_same_length(list_cache):
    assert list_cache.matches_result([1, 2, 3])


def test_list_cache_does_not_match_result_of_list_type_and_different_length(list_cache):
    assert not list_cache.matches_result([1, 2, 3, 4])


def test_list_cache_does_not_match_result_of_non_list_type(list_cache):
    assert not list_cache.matches_result({1, 2, 3})


def test_list_cache_starts_invalid(list_cache):
    uncached_paths = list_cache.get_uncached_paths([])

    assert_uncached_paths_popped_out_falses_in_list(uncached_paths, [False, False, False])


def test_list_cache_set_valid_makes_uncached_paths_empty(list_cache):
    list_cache.set_valid_value_at_path([], [2, 3, 4])
    uncached_paths = list_cache.get_uncached_paths([])

    assert len(uncached_paths) == 0


def test_list_cache_set_invalid_all_makes_uncached_paths_return_all(list_cache):
    list_cache.set_valid_value_at_path([], [2, 3, 4])
    list_cache.set_invalid_at_path([])
    uncached_paths = list_cache.get_uncached_paths([])

    assert_uncached_paths_popped_out_falses_in_list(uncached_paths, [False, False, False])


def test_list_cache_set_invalid_on_index_makes_uncached_paths_return_index(list_cache):
    list_cache.set_valid_value_at_path([], [2, 3, 4])
    list_cache.set_invalid_at_path([PathComponent(indexed_cls=list, component=1)])
    uncached_paths = list_cache.get_uncached_paths([])

    assert_uncached_paths_popped_out_falses_in_list(uncached_paths, [True, False, True])


def test_list_cache_set_invalid_on_slice_makes_uncached_paths_return_slice(list_cache):
    list_cache.set_valid_value_at_path([], [2, 3, 4])
    list_cache.set_invalid_at_path([PathComponent(indexed_cls=list, component=slice(1, 3))])
    uncached_paths = list_cache.get_uncached_paths([])

    assert_uncached_paths_popped_out_falses_in_list(uncached_paths, [True, False, False])


def test_list_cache_set_invalid_on_slice_with_end_none_makes_uncached_paths_return_slice(list_cache):
    list_cache.set_valid_value_at_path([], [2, 3, 4])
    list_cache.set_invalid_at_path([PathComponent(indexed_cls=list, component=slice(1, None, None))])
    uncached_paths = list_cache.get_uncached_paths([])

    assert_uncached_paths_popped_out_falses_in_list(uncached_paths, [True, False, False])


def test_list_cache_set_invalid_on_slice_with_start_none_makes_uncached_paths_return_slice(list_cache):
    list_cache.set_valid_value_at_path([], [2, 3, 4])
    list_cache.set_invalid_at_path([PathComponent(indexed_cls=list, component=slice(None, 2, None))])
    uncached_paths = list_cache.get_uncached_paths([])

    assert_uncached_paths_popped_out_falses_in_list(uncached_paths, [False, False, True])
