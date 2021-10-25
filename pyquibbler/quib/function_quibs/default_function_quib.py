from sys import getsizeof
from time import perf_counter
from typing import Callable, Any, Mapping, Tuple, Optional, List, TYPE_CHECKING

from pyquibbler.quib.function_quibs.cache import create_cache
from pyquibbler.quib.function_quibs.cache.shallow.shallow_cache import CacheStatus
from .function_quib import FunctionQuib, CacheBehavior
from ..assignment import AssignmentTemplate
from ..assignment.utils import get_sub_data_from_object_in_path

if TYPE_CHECKING:
    from ..assignment.assignment import PathComponent, PathComponent


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
        self._cache = None

    def _ensure_cache_matches_result(self, new_result: Any):
        if self._cache is None or not self._cache.matches_result(new_result):
            self._cache = create_cache(new_result)
        return self._cache

    def _invalidate_self(self, path: List['PathComponent']):
        if self._cache is not None:
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
        if self._cache is not None:
            try:
                uncached_paths = self._cache.get_uncached_paths(path)
            except (TypeError, IndexError):
                # It's possible the user is requesting a value at index which our current cache does not have but which
                # will exist after rerunning the function- in that case, return that nothing is cached
                if path is not None:
                    uncached_paths = [[]]
                else:
                    uncached_paths = []
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
            new_path = [*path[0:1]]
        return new_path

    def _get_inner_value_valid_at_path(self, path: Optional[List['PathComponent']]):
        """
        If the cached result is still valid, return it.
        Otherwise, calculate the value, store it in the cache and return it.
        """
        new_path = self._truncate_path_to_match_shallow_caches(path)
        uncached_paths = self._get_uncached_paths_matching_path(new_path)

        start_time = perf_counter()

        if len(uncached_paths) == 0:
            return self._cache.get_value()

        result = None
        for uncached_path in uncached_paths:
            result = self._call_func(uncached_path)

            elapsed_seconds = perf_counter() - start_time

            if new_path is not None and self._should_cache(result, elapsed_seconds):

                self._ensure_cache_matches_result(result)
                self._cache.set_valid_value_at_path(new_path, get_sub_data_from_object_in_path(result,
                                                                                           new_path))
                # sanity
                assert len(self._cache.get_uncached_paths(new_path)) == 0

        return result
