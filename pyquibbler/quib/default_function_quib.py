from sys import getsizeof
from time import perf_counter
from typing import Set, List, Callable, Any, Mapping, Tuple

from .function_quib import FunctionQuib
from .quib import Quib


class DefaultFunctionQuib(FunctionQuib):
    """
    The default implementation for a function quib, when no specific function quib type can be used.
    This implementation treats the quib as a whole unit, so when a dependency of a DefaultFunctionQuib
    is changed, the whole cache is thrown away.
    """

    def __init__(self,
                 artists_redrawers: Set,
                 children: List[Quib],
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 is_cache_valid: bool = False,
                 cached_result: Any = None):
        super().__init__(artists_redrawers=artists_redrawers, children=children, func=func, args=args, kwargs=kwargs)
        self._is_cache_valid = is_cache_valid
        self._cached_result = cached_result

    @property
    def is_cache_valid(self):
        """
        User interface to check cache validity.
        """
        return self._is_cache_valid

    def _invalidate(self):
        self._is_cache_valid = False

    def _should_cache(self, result: Any, elapsed_seconds: float):
        """
        Decide if the result of the calculation is worth caching according to its size and the calculation time.
        Note that there is no accurate way (and no efficient way to even approximate) the complete size of composite
        types in python, so we only measure the outer size of the object.
        """
        return elapsed_seconds > self.MIN_SECONDS_FOR_CACHE \
               and getsizeof(result) / elapsed_seconds < self.MAX_BYTES_PER_SECOND

    def get_value(self):
        """
        If the cached result is still valid, return it.
        Otherwise, calculate the value, store it in the cache and return it.
        """
        if self._is_cache_valid:
            return self._cached_result

        start_time = perf_counter()
        result = self._call_func()
        elapsed_seconds = perf_counter() - start_time
        if self._should_cache(result, elapsed_seconds):
            self._cached_result = result
            self._is_cache_valid = True
        return result
