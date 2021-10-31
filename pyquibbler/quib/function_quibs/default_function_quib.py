from __future__ import annotations
from sys import getsizeof
from time import perf_counter
from typing import Callable, Any, Mapping, Tuple, Optional, List, TYPE_CHECKING

import numpy as np

from pyquibbler.quib.function_quibs.cache import create_cache
from .cache.cache import CacheStatus
from .cache.holistic_cache import PathCannotHaveComponentsException
from .cache.shallow.indexable_cache import transform_cache_to_nd_if_necessary_given_path
from .function_quib import FunctionQuib, CacheBehavior
from ..assignment import AssignmentTemplate
from ..assignment.utils import get_sub_data_from_object_in_path
from ...env import IS_IN_INVALIDATION

if TYPE_CHECKING:
    from ..assignment.assignment import PathComponent


class DefaultFunctionQuib(FunctionQuib):
    """
    The default implementation for a function quib, when no specific function quib type can be used.
    This implementation treats the quib as a whole unit, so when a dependency of a DefaultFunctionQuib
    is changed, the whole cache is thrown away.
    """

    @property
    def cache_status(self):
        """
        User interface to check cache validity.
        """
        return self._cache.get_cache_status() if self._cache is not None else CacheStatus.ALL_INVALID

    def __init__(self,
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior],
                 assignment_template: Optional[AssignmentTemplate] = None):
        super().__init__(func, args, kwargs, cache_behavior, assignment_template=assignment_template)
        self._reset_cache()
        self._was_invalidated = False

    def _reset_cache(self):
        self._cache = None
        self._shape = None
        self._type = None
        self._caching = True if self._cache_behavior == CacheBehavior.ON else False

    def _ensure_cache_matches_result(self, new_result: Any):
        """
        Ensure there exists a current cache matching the given result; if the held cache does not match,
        this function will now recreate the cache to match it
        """
        if self._cache is None or not self._cache.matches_result(new_result):
            self._cache = create_cache(new_result)
        return self._cache

    def _invalidate_self(self, path: List['PathComponent']):
        if len(path) == 0:
            self._reset_cache()

        if self._cache is not None:
            self._cache = transform_cache_to_nd_if_necessary_given_path(self._cache, path)
            self._cache.set_invalid_at_path(path)

    def _should_cache(self, result: Any, elapsed_seconds: float):
        """
        Decide if the result of the calculation is worth caching according to its size and the calculation time.
        Note that there is no accurate way (and no efficient way to even approximate) the complete size of composite
        types in python, so we only measure the outer size of the object.
        """
        if self._cache_behavior is CacheBehavior.ON:
            return True
        if self._cache_behavior is CacheBehavior.OFF:
            return False
        assert self._cache_behavior is CacheBehavior.AUTO, \
            f'self._cache_behavior has unexpected value: "{self._cache_behavior}"'
        return elapsed_seconds > self.MIN_SECONDS_FOR_CACHE \
            and getsizeof(result) / elapsed_seconds < self.MAX_BYTES_PER_SECOND

    def _get_uncached_paths_matching_path(self, path: Optional[List['PathComponent']]):
        """
        Get a list of paths that are uncached within the given path- these paths must be a subset of the given path
        (or the path itself)
        """

        if self._cache is not None:

            if path is None:
                # We need to be valid at no paths, so by definitions we also have no uncached paths that match no paths
                return []

            try:
                uncached_paths = self._cache.get_uncached_paths(path)
            except (TypeError, IndexError):
                # It's possible the user is requesting a value at index which our current cache does not have but which
                # will exist after rerunning the function- in that case, return that the given path is not cached
                uncached_paths = [path]
        else:
            uncached_paths = [path]

        return uncached_paths

    def _truncate_path_to_match_shallow_caches(self, path: Optional[List['PathComponent']]):
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

    def _run_func_on_uncached_paths(self, truncated_path: List[PathComponent],
                                    uncached_paths: List[List[PathComponent]]):
        """
        Run the function a list of uncached paths, given an original truncated path, storing it in our cache
        """
        result = None
        for uncached_path in uncached_paths:
            result = self._call_func(uncached_path)

            self._ensure_cache_matches_result(result)
            if uncached_path is not None:
                try:
                    valid_value = get_sub_data_from_object_in_path(result, truncated_path)
                    self._cache = transform_cache_to_nd_if_necessary_given_path(self._cache, truncated_path)
                    self._cache.set_valid_value_at_path(truncated_path, valid_value)
                    # We need to get the result from the cache (as opposed to simply using the last run), since we
                    # don't want to only take the last run
                    result = self._cache.get_value()
                except PathCannotHaveComponentsException:
                    # We do not have a diverged cache for this type, we can't store the value; this is not a problem as
                    # everything will work as expected, but we will simply not cache
                    assert len(uncached_paths) == 1, "There should never be a situation in which we have multiple " \
                                                     "uncached paths but our cache can't handle setting a value at a " \
                                                     "specific component"
                    break
                else:
                    # sanity
                    assert len(self._cache.get_uncached_paths(truncated_path)) == 0

        return result

    def _get_inner_value_valid_at_path(self, path: Optional[List['PathComponent']]):
        """
        If the cached result is still valid, return it.
        Otherwise, calculate the value, store it in the cache and return it.
        """
        truncated_path = self._truncate_path_to_match_shallow_caches(path)
        uncached_paths = self._get_uncached_paths_matching_path(truncated_path)

        if len(uncached_paths) == 0:
            return self._cache.get_value()

        start_time = perf_counter()
        result = self._run_func_on_uncached_paths(truncated_path, uncached_paths)
        elapsed_seconds = perf_counter() - start_time

        if self._should_cache(result, elapsed_seconds):
            self._caching = True
        if not self._caching:
            self._cache = None

        return result

    def set_cache_behavior(self, cache_behavior: CacheBehavior):
        super(DefaultFunctionQuib, self).set_cache_behavior(cache_behavior)
        if cache_behavior == CacheBehavior.OFF:
            self._reset_cache()
