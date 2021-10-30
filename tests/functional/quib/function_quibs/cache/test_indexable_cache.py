import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import IndexableCache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from tests.functional.quib.function_quibs.cache.cache_test import IndexableCacheTest


@pytest.mark.parametrize("result", [
    (1, 2, 3),
    [1, 2, 3],
])
class TestIndexableCache(IndexableCacheTest):

    cls = IndexableCache
    unsupported_type_result = {1, 2, 3}

    paths = [
        [],
        [0],
        [1],
        [slice(1, None, None)],
        [slice(None, 2, None)],
        [slice(1, 3, None)],
        [slice(None, 2, 3)]
    ]

    @pytest.fixture()
    def valid_value(self):
        return 1

    def get_values_from_result(self, result):
        return result if isinstance(result, (list, tuple)) else [result]

    def get_result_with_all_values_set_to_value(self, result, value):
        return type(result)([value for _ in result])

    def get_result_with_value_broadcasted_to_path(self, obj, path, value):
        new_value = list(obj)
        if len(path) == 0:
            new_value = [value for _ in obj]
        else:
            working_indices = path[0].component
            if isinstance(working_indices, slice):
                length_to_broadcast = len(obj[working_indices])
                new_value[working_indices] = [value for _ in range(length_to_broadcast)]
            else:
                new_value[working_indices] = value
        return type(obj)(new_value)

    def test_list_cache_does_not_match_result_of_list_type_and_different_length(self, cache):
        assert not cache.matches_result([1, 2, 3, 4])

    def test_cache_get_cache_status_on_partial(self, cache):
        cache.set_valid_value_at_path([PathComponent(indexed_cls=list, component=slice(1, None, None))], [10, 10])
    
        assert cache.get_cache_status() == CacheStatus.PARTIAL

    def test_list_cache_get_cache_status_when_completely_invalid_piece_by_piece(self, cache):
        cache.set_valid_value_at_path([], [10, 10, 10])
    
        cache.set_invalid_at_path([PathComponent(component=0, indexed_cls=list)])
        cache.set_invalid_at_path([PathComponent(component=1, indexed_cls=list)])
        cache.set_invalid_at_path([PathComponent(component=2, indexed_cls=list)])

        assert cache.get_cache_status() == CacheStatus.ALL_INVALID

    def test_cache_set_valid_makes_uncached_paths_empty(self, result, cache):
        cache.set_valid_value_at_path([], result)
        uncached_paths = cache.get_uncached_paths([])

        assert len(uncached_paths) == 0

    def test_cache_set_valid_partial_and_get_uncached_paths(self, cache, result, valid_components, uncached_path_components, valid_value):
        super(TestIndexableCache, self).test_cache_set_valid_partial_and_get_uncached_paths(cache,
                                                                                            result, valid_components,
                                                                                            uncached_path_components,
                                                                                            valid_value)

    def test_cache_set_invalid_partial_and_get_uncached_paths(self, cache, result, invalid_components,
                                                              uncached_path_components):
        super(TestIndexableCache, self).test_cache_set_invalid_partial_and_get_uncached_paths(cache, result,
                                                                                              invalid_components,
                                                                                              uncached_path_components)

    def set_completely_invalid(self, result, cache):
        for i in range(len(result)):
            cache.set_invalid_at_path([PathComponent(component=i, indexed_cls=type(result))])
