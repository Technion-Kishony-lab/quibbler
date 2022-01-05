from typing import List, Optional, Any

import numpy as np

from pyquibbler.refactor.path import Path
from pyquibbler.refactor.path.data_accessing import deep_get, deep_assign_data_in_path
from pyquibbler.refactor.cache import create_cache, HolisticCache, NdUnstructuredArrayCache
from pyquibbler.refactor.cache.cache import Cache
from pyquibbler.refactor.cache.holistic_cache import PathCannotHaveComponentsException
from pyquibbler.refactor.cache.shallow.indexable_cache import transform_cache_to_nd_if_necessary_given_path
from pyquibbler.refactor.function_definitions.func_call import FuncCall
from pyquibbler.refactor.quib.utils import call_func_with_quib_values


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


def run_func_on_uncached_paths(cache: Optional[Cache],
                               func_call: FuncCall,
                               truncated_path: Path,
                               uncached_paths: List[Optional[Path]]):
    """
    Run the function a list of uncached paths, given an original truncated path, storing it in our cache
    """
    for uncached_path in uncached_paths:
        result = call_func_with_quib_values(func_call.func,
                                            args=func_call.args_values.args,
                                            kwargs=func_call.args_values.kwargs)

        cache = _ensure_cache_matches_result(cache, result)

        if uncached_path is not None:
            try:
                cache = transform_cache_to_nd_if_necessary_given_path(cache, truncated_path)
                value = get_cached_data_at_truncated_path_given_result_at_uncached_path(cache, 
                                                                                        result, 
                                                                                        truncated_path, 
                                                                                        uncached_path)

                cache.set_valid_value_at_path(truncated_path, value)
            except PathCannotHaveComponentsException:
                # We do not have a diverged cache for this type, we can't store the value; this is not a problem as
                # everything will work as expected, but we will simply not cache
                assert len(uncached_paths) == 1, "There should never be a situation in which we have multiple " \
                                                 "uncached paths but our cache can't handle setting a value at a " \
                                                 "specific component"
                break
            else:
                # sanity
                assert len(cache.get_uncached_paths(truncated_path)) == 0

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
    

def _get_uncached_paths_matching_path(cache: Optional[Cache], path: [List['PathComponent']]):
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
