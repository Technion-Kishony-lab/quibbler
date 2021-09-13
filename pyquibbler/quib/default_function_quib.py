from operator import getitem
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

    def get_value(self):
        """
        If the cached result is still valid, return it.
        Otherwise, calculate the value, store it in the cache and return it.
        """
        if self._is_cache_valid:
            return self._cached_result

        result = self._call_func()
        self._cached_result = result
        self._is_cache_valid = True
        return result


# We want quibs' __getitem__ to return a function quib representing the __getitem__ operation,
# so if the original quib is changed, whoever called __getitem__ will be invalidated.
Quib.__getitem__ = DefaultFunctionQuib.create_wrapper(getitem)
