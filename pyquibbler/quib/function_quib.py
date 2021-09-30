from __future__ import annotations
from enum import Enum
from functools import wraps
from typing import List, Callable, Any, Mapping, Tuple, Optional

from .assignment_template import AssignmentTemplate
from .quib import Quib
from .utils import is_there_a_quib_in_args, iter_quibs_in_args, call_func_with_quib_values, \
    deep_copy_without_quibs_or_artists


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
    _DEFAULT_CACHE_BEHAVIOR = CacheBehavior.AUTO
    MAX_BYTES_PER_SECOND = 2 ** 30
    MIN_SECONDS_FOR_CACHE = 1e-3

    def __init__(self,
                 func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior],
                 assignment_template: Optional[AssignmentTemplate] = None):
        super().__init__(assignment_template=assignment_template)
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._cache_behavior = None

        if cache_behavior is None:
            cache_behavior = self._DEFAULT_CACHE_BEHAVIOR
        self.set_cache_behavior(cache_behavior)

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, **kwargs):
        """
        Public constructor for FunctionQuib.
        """
        if func_kwargs is None:
            func_kwargs = {}
        else:
            func_kwargs = {
                k: deep_copy_without_quibs_or_artists(v)
                for k, v
                in func_kwargs.items()
            }
        func_args = deep_copy_without_quibs_or_artists(tuple(arg for arg in func_args))
        self = cls(func=func, args=func_args, kwargs=func_kwargs,
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

    def __repr__(self):
        return f"<{self.__class__.__name__} - {self._func}>"

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

    def _get_dependencies(self) -> List[Quib]:
        """
        A utility for debug purposes.
        Returns a list of quibs that this quib depends on.
        """
        return iter_quibs_in_args(self._args, self._kwargs)
