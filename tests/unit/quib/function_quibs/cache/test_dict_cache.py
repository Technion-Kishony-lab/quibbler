import pytest

from pyquibbler.quib.function_quibs.cache import DictShallowCache


@pytest.fixture
def dict_cache():
    return DictShallowCache.create_from_result({"a": 1})


def test_dict_cache_matches_result_of_dict_type_and_same_keys(dict_cache):
    assert dict_cache.matches_result({"a": 2})


def test_dict_cache_doesnt_match_result_of_non_dict_type(dict_cache):
    assert not dict_cache.matches_result([1, 2, 3])


def test_dict_cache_doesnt_match_result_of_different_keys(dict_cache):
    assert not dict_cache.matches_result({"b": 2})
