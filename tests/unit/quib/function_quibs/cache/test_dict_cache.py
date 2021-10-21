import pytest

from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.function_quibs.cache import DictShallowCache
from tests.unit.quib.function_quibs.cache.abc_test_cache import ABCTestIndexableCache


def assert_uncached_paths_had_exact_keys(uncached_paths, keys):
    keys_to_pop = set(keys)
    for path in uncached_paths:
        assert len(path) == 1
        inner_component = path[0].component
        assert inner_component in keys_to_pop, f"The key {inner_component} was in the paths but was not expected"
        keys_to_pop.remove(inner_component)

    assert len(keys_to_pop) == 0, f"The keys {keys_to_pop} were expected but not in the paths"


class TestDictCache(ABCTestIndexableCache):

    cls = DictShallowCache
    result = {"a": 1, "b": 2, "c": 3}
    unsupported_type_result = [1, 2, 3]
    empty_result = {}

    def test_cache_set_valid_partial(self, cache: DictShallowCache):
        cache.set_valid_value_at_path([PathComponent(component="a", indexed_cls=dict)], value="22")
        uncached_paths = cache.get_uncached_paths([])

        assert_uncached_paths_had_exact_keys(uncached_paths, ["b", "c"])

    def test_cache_set_invalid_partial(self, cache):
        pass

    def test_cache_get_cache_status_on_partial(self, cache):
        pass
