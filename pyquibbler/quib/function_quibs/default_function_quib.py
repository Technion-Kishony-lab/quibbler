from enum import Enum
from sys import getsizeof
from time import perf_counter
from typing import Callable, Any, Mapping, Tuple, Optional, List, TYPE_CHECKING

from .cache import ShallowCache, create_cache
from .function_quib import FunctionQuib, CacheBehavior
from ..assignment import AssignmentTemplate
from ..assignment.utils import get_sub_data_from_object_in_path

if TYPE_CHECKING:
    from ..assignment.assignment import PathComponent, Assignment, PathComponent
    from ..quib import Quib


class CacheStatus(Enum):
    FALSE = 0
    TRUE = 1
    PARTIAL = 2


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
        if self._cache.is_valid_at_path([]):
            return CacheStatus.TRUE
        elif not self._cache.is_valid_at_path(None):
            return CacheStatus.FALSE
        else:
            return CacheStatus.PARTIAL

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
        if len(path) == 0:
            self._cache.set_invalid_at_key()
        self._cache.set_valid_value_at_key(path[0])

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

    def _get_inner_value_valid_at_path(self, path: Optional[List['PathComponent']]):
        """
        If the cached result is still valid, return it.
        Otherwise, calculate the value, store it in the cache and return it.
        """
        # Because we have a shallow cache, we want the result valid at the first component
        if path is None:
            new_path = None
        elif len(path) == 0:
            new_path = []
        else:
            new_path = [path[0]]

        # TODO: comment explaining
        uncached_paths = self._cache.get_uncached_paths(new_path) if self._cache else [new_path]
        start_time = perf_counter()

        # TODO: what if we don't store cache??
        for uncached_path in uncached_paths:
            result = self._call_func(uncached_path)

            elapsed_seconds = perf_counter() - start_time
            self._ensure_cache_matches_result(result)

            if new_path is not None: #$and self._should_cache(result, elapsed_seconds):

                self._cache.set_valid_value_at_path(new_path, get_sub_data_from_object_in_path(result,
                                                                                           new_path))
        return self._cache.get_value()
