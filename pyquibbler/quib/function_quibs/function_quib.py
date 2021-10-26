from __future__ import annotations


import numpy as np
import types
from enum import Enum
from functools import wraps, cached_property, partial, lru_cache
from typing import Callable, Any, Mapping, Tuple, Optional, Set, List, Union, Dict
from functools import wraps, cached_property, lru_cache
from typing import Callable, Any, Mapping, Tuple, Optional, Set, List

from ..override_choice import get_overrides_for_assignment
from ..assignment import AssignmentTemplate, Assignment, PathComponent, QuibWithAssignment
from ..quib import Quib
from ..utils import is_there_a_quib_in_args, iter_quibs_in_args, call_func_with_quib_values, \
    deep_copy_without_quibs_or_artists, copy_and_convert_args_and_kwargs_to_values, \
    iter_args_and_names_in_function_call, \
    recursively_run_func_on_object, QuibRef, copy_and_convert_kwargs_to_values
from ...env import LAZY, PRETTY_REPR
from ...env import LAZY


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
    def parents(self) -> Set[Quib]:
        return set(iter_quibs_in_args(self.args, self.kwargs))

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
        if not LAZY:
            self.get_value()
        return self

    @classmethod
    def _add_ufunc_members_to_wrapper(cls, func: Callable, quib_supporting_func_wrapper: Callable):
        """
        Numpy ufuncs have members used internally by numpy and could also be used by users.
        This function members attributes to ufunc wrappers so they could be used as ufuncs.
        """
        for member in dir(func):
            if not member.startswith('_'):
                val = getattr(func, member)
                if callable(val):
                    val = cls.create_wrapper(val)
                setattr(quib_supporting_func_wrapper, member, val)

    @classmethod
    def _wrapper_call(cls, func, args, kwargs):
        """
        The actual code that runs when a quib-supporting function wrapper is called.
        """
        if is_there_a_quib_in_args(args, kwargs):
            return cls.create(func=func, func_args=args, func_kwargs=kwargs)

        return func(*args, **kwargs)

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
            return cls._wrapper_call(func, args, kwargs)

        quib_supporting_func_wrapper.__annotations__['return'] = cls
        quib_supporting_func_wrapper.__quib_wrapper__ = cls
        if isinstance(func, np.ufunc):
            cls._add_ufunc_members_to_wrapper(func, quib_supporting_func_wrapper)
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

    def assign(self, assignment: Assignment) -> None:
        """
        Apply the given assignment to the function quib.
        Using inverse assignments, the assignment will propagate as far is possible up the dependency graph,
        and collect possible overrides.
        When more than one override can be performed, the user will be asked to choose one.
        When there is only one override option, it will be automatically performed.
        When there are no override options, AssignmentNotPossibleException is raised.
        """
        get_overrides_for_assignment(self, assignment).apply()

    def __repr__(self):
        if PRETTY_REPR:
            return self.pretty_repr()
        return f"<{self.__class__.__name__} - {getattr(self.func, '__name__', repr(self.func))}>"

    def pretty_repr(self):
        func_name = getattr(self.func, '__name__', str(self.func))
        args, kwargs = copy_and_convert_args_and_kwargs_to_values(self.args, self.kwargs)
        posarg_reprs = map(str, args)
        kwarg_reprs = (f'{key}={val}' for key, val in kwargs.items())
        return f'{func_name}({", ".join([*posarg_reprs, *kwarg_reprs])})'

    def get_cache_behavior(self):
        return self._cache_behavior

    def set_cache_behavior(self, cache_behavior: CacheBehavior):
        self._cache_behavior = cache_behavior

    def _get_source_paths_of_quibs_given_path(self, path: List[PathComponent]) -> Dict[Quib, str]:
        """
        Get a mapping of argument data source quibs to their respective paths that influenced the given path (`path`)
        """
        return {}

    def _call_func(self, valid_path: Optional[List[PathComponent]]):
        """
        Call the function wrapped by this FunctionQuib with the
        given arguments after replacing quib with their values.

        The result should be valid at valid_path- the default implementation is to always get a result that's value
        for all paths (not diverged), which will necessarily be also valid at `valid_path`.
        This function can and should be overriden if there is a more specific implementation for getting a value only
        valid at valid_path
        """
        new_args = []
        if valid_path is None:
            quibs_to_paths = {}
        else:
            quibs_to_paths = self._get_source_paths_of_quibs_given_path(valid_path)
        for i, arg in enumerate(self.args):
            def _replace_potential_quib_with_value(inner_arg: Union[Quib, Any]):
                if isinstance(inner_arg, QuibRef):
                    return inner_arg.quib
                if not isinstance(inner_arg, Quib):
                    return inner_arg
                path = quibs_to_paths.get(inner_arg, None if valid_path is None else [])
                return inner_arg.get_value_valid_at_path(path)

            new_args.append(recursively_run_func_on_object(_replace_potential_quib_with_value, arg))

        return self._func(*new_args, **copy_and_convert_kwargs_to_values(self.kwargs))

    def get_inversions_for_assignment(self, assignment: Assignment) -> List[QuibWithAssignment]:
        """
        Get a list of inversions to parent quibs for a given assignment
        """
        return []

    @lru_cache()
    def _get_all_args_dict(self, default_to_args_kwargs_on_no_signature=True, include_defaults=True):
        try:
            return dict(iter_args_and_names_in_function_call(self.func, self.args, self.kwargs, include_defaults))
        except ValueError:
            if default_to_args_kwargs_on_no_signature:
                return {'args': self.args, 'kwargs': self.kwargs}
            raise

    def _get_arg_values_by_position(self) -> List[Any]:
        """
        Try to return all args values by position, including kwargs. If the signature is unknown, just return the args.
        """
        try:
            args_iterable = self._get_all_args_dict(False, False).values()
        except ValueError:
            args_iterable = self.args
        return list(args_iterable)
