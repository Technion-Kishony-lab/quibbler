from __future__ import annotations
from typing import Optional, Any

from pyquibbler.path import deep_get, deep_set, Path, Paths
from .cache import Cache
from .holistic_cache import HolisticCache


def get_cached_data_at_truncated_path_given_result_at_uncached_path(cache, result, truncated_path, uncached_path):
    data = cache.get_value()

    valid_value = deep_get(result, uncached_path)

    if isinstance(cache, HolisticCache):
        value = valid_value
    else:
        new_data = deep_set(data, uncached_path, valid_value)
        value = deep_get(new_data, truncated_path)

    return value


def ensure_cache_matches_result(cache: Optional[Cache], new_result: Any) -> Cache:
    """
    Ensure there exists a current cache matching the given result; if the held cache does not match,
    this function will now recreate the cache to match it
    """
    from pyquibbler.cache import create_cache
    if cache is None or not cache.matches_result(new_result):
        cache = create_cache(new_result)
    return cache


def truncate_path_to_match_shallow_caches(path: Optional[Path], result):
    """
    Truncate a path so it can be used by shallow caches- we only want to cache and store elements at their first
    component in their path
    """
    if path is None:
        return None

    if len(path) == 0:
        return []

    if len(path) >= 2 and path[0].referencing_field_in_field_array(type(result)):
        # We are in a situation in which we have a field, and then indexes- these are always interchangeable
        # by definition, so we switch them to get the indexes in order to behave in the same fashion-
        # e.g. ["a"][0] or [0]["a"] should cache in the same fashion (for an ndarray), namely as [0]
        return [path[1]]
    return [path[0]]


def get_uncached_paths_matching_path(cache: Optional[Cache], path: Path) -> Paths:
    """
    Get a list of paths that are uncached within the given path- these paths must be a subset of the given path
    (or the path itself)
    """

    if cache is None:
        return [path]

    if path is None:
        # We need to be valid at no paths, so by definitions we also have no uncached paths that match no paths
        return []

    try:
        return cache.get_uncached_paths(path)
    except (TypeError, IndexError):
        # It's possible the user is requesting a value at index which our current cache does not have but which
        # will exist after rerunning the function- in that case, return that the given path is not cached
        return [path]
