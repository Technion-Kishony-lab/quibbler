import pytest

from pyquibbler.quib.function_quibs.cache import ListShallowCache


@pytest.fixture
def list_cache():
    return ListShallowCache.create_from_result([1, 2, 3])


def test_list_cache_matches_result_of_list_type_and_same_length(list_cache):
    assert list_cache.matches_result([1, 2, 3])


def test_list_cache_does_not_match_result_of_list_type_and_different_length(list_cache):
    assert not list_cache.matches_result([1, 2, 3, 4])


def test_list_cache_does_not_match_result_of_non_list_type(list_cache):
    assert not list_cache.matches_result({1, 2, 3})

