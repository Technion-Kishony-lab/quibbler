from __future__ import annotations
import types
from pyquibbler.quib.assignment.reverse_assignment import get_override_options
from enum import Enum
from functools import wraps, cached_property
from typing import List, Callable, Any, Mapping, Tuple, Optional, Set

from .utils import choose_override_dialog
from ..assignment import AssignmentTemplate, Assignment
from ..assignment.assignment import QuibWithAssignment
from ..quib import Quib
from ..utils import is_there_a_quib_in_args, iter_quibs_in_args, call_func_with_quib_values, \
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

    @cached_property
    def ancestors(self) -> Set[Quib]:
        """
        Return all ancestors of the quib, going recursively up the tree
        """
        all_ancestors = set()
        for quib in iter_quibs_in_args(self._args, self._kwargs):
            all_ancestors.add(quib)
            if isinstance(quib, FunctionQuib):
                all_ancestors |= quib.ancestors
        return all_ancestors

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, **kwargs):
        """
        Public constructor for FunctionQuib.
        """
        # If we received a function that was already wrapped with a function quib, we want want to unwrap it
        while hasattr(func, '__quib_wrapper__'):
            assert func.__quib_wrapper__ is cls, "This function was wrapped previously with a different class"
            previous_func = func
            func = func.__wrapped__
            # If it was a bound method we need to recreate it
            if hasattr(previous_func, '__self__'):
                func = types.MethodType(func, previous_func.__self__)

        if func_kwargs is None:
            func_kwargs = {}
        func_kwargs = {k: deep_copy_without_quibs_or_artists(v)
                       for k, v in func_kwargs.items()}
        func_args = deep_copy_without_quibs_or_artists(func_args)
        self = cls(func=func, args=func_args, kwargs=func_kwargs,
                   cache_behavior=cache_behavior, **kwargs)
        for arg in iter_quibs_in_args(func_args, func_kwargs):
            arg.add_child(self)
        return self

    @classmethod
    def create_wrapper(cls, func: Callable):
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

        quib_supporting_func_wrapper.__annotations__['return'] = cls
        quib_supporting_func_wrapper.__quib_wrapper__ = cls
        return quib_supporting_func_wrapper

    @property
    def func(self):
        return self._func

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    def _choose_and_apply_overrides(self, override_options, diverged_options):
        if override_options:
            if len(override_options) == 1 and not diverged_options:
                chosen_override = override_options[0]
            else:
                chosen_override = choose_override_dialog(override_options, len(diverged_options) > 0)
            if chosen_override is not None:
                chosen_override.quib._override(chosen_override.assignment)
                return

        assert diverged_options
        for next_override_options, next_diverged_options in diverged_options:
            self._choose_and_apply_overrides(next_override_options, next_diverged_options)

    def assign(self, assignment: Assignment) -> None:
        override_options, diverged_options = get_override_options(QuibWithAssignment(self, assignment))
        self._choose_and_apply_overrides(override_options, diverged_options)

    def __repr__(self):
        return f"<{self.__class__.__name__} - {self.func}>"

    def get_cache_behavior(self):
        return self._cache_behavior

    def set_cache_behavior(self, cache_behavior: CacheBehavior):
        self._cache_behavior = cache_behavior

    def _call_func(self):
        """
        Call the function wrapped by this FunctionQuib with the
        given arguments after replacing quib with their values.
        """
        return call_func_with_quib_values(self.func, self.args, self.kwargs)

    def _get_dependencies(self) -> List[Quib]:
        """
        A utility for debug purposes.
        Returns a list of quibs that this quib depends on.
        """
        return iter_quibs_in_args(self.args, self.kwargs)
