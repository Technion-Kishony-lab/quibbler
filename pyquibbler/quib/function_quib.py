from copy import deepcopy
from enum import Enum
from functools import wraps
from typing import Set, List, Callable, Any, Mapping, Tuple, Optional

from .quib import Quib
from .utils import is_there_a_quib_in_args, iter_quibs_in_args, call_func_with_quib_values


class CacheBehavior(Enum):
    """
    The different modes in which the caching of a FunctionQuib can operate:
     - `AUTO`: decide automatically according to the ratio between evaluation time and memory consumption.
     - `OFF`: never cache.
     - `ON`: always cache.
    """
    AUTO = 'auto'
    OFF = 'off'
    ON = 'on'


class FunctionQuib(Quib):
    """
    An abstract class for quibs that represent the result of a computation.
    """
    DEFAULT_CACHE_BEHAVIOR = CacheBehavior.AUTO
    MAX_BYTES_PER_SECOND = 2 ** 30
    def __init__(self,
                 artists_redrawers: Set,
                 children: Set[Quib],
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior]):
        super().__init__(artists_redrawers, children)
        self._func = func
        self._args = args
        self._kwargs = kwargs
        if cache_behavior is None:
            cache_behavior = self.DEFAULT_CACHE_BEHAVIOR
        self.set_cache_behavior(cache_behavior)

    MIN_SECONDS_FOR_CACHE = 1e-3

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, **kwargs):
        """
        Public constructor for FunctionQuib.
        """
        if func_kwargs is None:
            func_kwargs = {}
        else:
            func_kwargs = deepcopy(func_kwargs)
        func_args = deepcopy(func_args)
        self = cls(artists_redrawers=set(), children=set(), func=func, args=func_args, kwargs=func_kwargs,
                   cache_behavior=cache_behavior, **kwargs)
        for arg in iter_quibs_in_args(func_args, func_kwargs):
            arg.add_child(self)
        return self

    @classmethod
    def create_wrapper(cls, func):
        """
        Given an original function, return a new function (a "wrapper") to be used instead of the original.
        The wrapper, when called, will return a FunctionQuib of type `cls` if its arguments contain a quib.
        Otherwise it will call the original function and will return its result.
        This function can be used as a decorator.
        """

        @wraps(func)
        def quib_supporting_func_wrapper(*args, **kwargs):
            if is_there_a_quib_in_args(args, kwargs):
                return cls.create(func=func, func_args=args, func_kwargs=kwargs)

            return func(*args, **kwargs)

        return quib_supporting_func_wrapper

    def get_cache_behavior(self):
        return self._cache_behavior

    def set_cache_behavior(self, cache_behavior: CacheBehavior):
        self._cache_behavior = cache_behavior

    def _call_func(self):
        """
        Call the function wrapped by this FunctionQuib with the
        given arguments after replacing quib with their values.
        """
        return call_func_with_quib_values(self._func, self._args, self._kwargs)

    def _get_dependencies(self) -> List['Quib']:
        """
        A utility for debug purposes.
        Returns a list of quibs that this quib depends on.
        """
        return iter_quibs_in_args(self._args, self._kwargs)
