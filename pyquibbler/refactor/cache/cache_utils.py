from typing import List, Optional, Any

import numpy as np

from pyquibbler.refactor.path.data_accessing import deep_get, deep_assign_data_in_path
from pyquibbler.refactor.cache import create_cache, HolisticCache, NdUnstructuredArrayCache
from pyquibbler.refactor.cache.cache import Cache


def get_cached_data_at_truncated_path_given_result_at_uncached_path(cache, result, truncated_path, uncached_path):
    data = cache.get_value()

    # Need to refactor this so that the cache itself takes care of these edge cases- for example,
    # indexablecache already knows how to take care of tuples, and holisticache knows not to try setting values at
    # specific paths.
    # Perhaps get_value(with_data_at_component)?
    # Or perhaps simply wait for deep caches...
    if isinstance(result, list) and isinstance(cache, NdUnstructuredArrayCache):
        result = np.array(result)

    valid_value = deep_get(result, uncached_path)

    if isinstance(data, tuple):
        new_data = deep_assign_data_in_path(list(data), uncached_path, valid_value)
        value = deep_get(tuple(new_data), truncated_path)
    else:
        if isinstance(cache, HolisticCache):
            value = valid_value
        else:
            new_data = deep_assign_data_in_path(data, uncached_path, valid_value)
            value = deep_get(new_data, truncated_path)

    return value


def _ensure_cache_matches_result(cache: Optional[Cache], new_result: Any):
    """
    Ensure there exists a current cache matching the given result; if the held cache does not match,
    this function will now recreate the cache to match it
    """
    if cache is None or not cache.matches_result(new_result):
        cache = create_cache(new_result)
    return cache


def _truncate_path_to_match_shallow_caches(path: Optional[List['PathComponent']]):
    """
    Truncate a path so it can be used by shallow caches- we only want to cache and store elements at their first
    component in their path
    """
    if path is None:
        new_path = None
    else:
        first_two_components = path[0:2]
        if (
                len(first_two_components) == 2
                and first_two_components[0].references_field_in_field_array()
                and not first_two_components[1].references_field_in_field_array()
                and first_two_components[1].indexed_cls == np.ndarray
        ):
            # We are in a situation in which we have a field, and then indexes- these are always interchangable
            # by definition, so we switch them to get the indexes in order to behave in the same fashion-
            # e.g.
            # ["a"][0] or [0]["a"] should cache in the same fashion (for an ndarray)
            new_path = [first_two_components[1]]
        else:
            new_path = [*first_two_components[0:1]]
    return new_path
    

def get_uncached_paths_matching_path(cache: Optional[Cache], path: [List['PathComponent']]):
    """
    Get a list of paths that are uncached within the given path- these paths must be a subset of the given path
    (or the path itself)
    """

    if cache is not None:
        if path is None:
            # We need to be valid at no paths, so by definitions we also have no uncached paths that match no paths
            return []

        try:
            uncached_paths = cache.get_uncached_paths(path)
        except (TypeError, IndexError):
            # It's possible the user is requesting a value at index which our current cache does not have but which
            # will exist after rerunning the function- in that case, return that the given path is not cached
            uncached_paths = [path]
    else:
        uncached_paths = [path]

    return uncached_paths
