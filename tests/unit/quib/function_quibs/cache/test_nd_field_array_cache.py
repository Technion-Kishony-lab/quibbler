import numpy as np

from pyquibbler.quib.function_quibs.cache.shallow.nd_cache import NdFieldArrayShallowCache
from tests.unit.quib.function_quibs.cache.cache_test import IndexableCacheTest


class TestNdFieldArrayCache(IndexableCacheTest):

    cls = NdFieldArrayShallowCache
    dtype = [("name", np.str_, 20), ("age", np.int_, 64)]
    result = np.array([("Maor", 24), ("Yossi", 15), ("Danahellilililili", 32)], dtype=dtype)

    unsupported_type_result = [1, 2, 3]
    empty_result = np.array([], dtype=dtype)
    set_valid_test_cases = []
    set_invalid_test_cases = []

    def assert_uncached_paths_match_expected_value(self, uncached_paths, expected_value):
        pass

    def test_cache_get_cache_status_on_partial(self, cache):
        pass

