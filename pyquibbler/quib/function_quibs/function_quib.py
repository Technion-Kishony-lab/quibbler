from __future__ import annotations
import functools
import pathlib
import numpy as np
import types
from dataclasses import dataclass
from enum import Enum
from typing import Union, Dict
from functools import wraps, cached_property, lru_cache
from typing import Callable, Any, Mapping, Tuple, Optional, Set, List

from .pretty_converters import MathExpression
from .external_call_failed_exception_handling import external_call_failed_exception_handling, \
    raise_quib_call_exceptions_as_own
from .utils import ArgsValues
from ..override_choice import get_override_group_for_change
from ..assignment import AssignmentTemplate, Assignment, PathComponent, AssignmentToQuib
from ..quib import Quib
from ..utils import is_there_a_quib_in_args, iter_quibs_in_args, deep_copy_without_quibs_or_artists, \
    recursively_run_func_on_object, QuibRef
from ...env import EVALUATE_NOW, PRETTY_REPR
from ...exceptions import PyQuibblerException
from ...input_validation_utils import validate_user_input


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


@dataclass
class UnknownCacheBehaviorException(PyQuibblerException):
    attempted_value: str

    def __str__(self):
        return f"{self.attempted_value} is not a valid value for a cache behavior"


class FunctionQuib(Quib):
    """
    An abstract class for quibs that represent the result of a computation.
    """
    _DEFAULT_EVALUATE_NOW = EVALUATE_NOW
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

        if cache_behavior is None:
            cache_behavior = self._DEFAULT_CACHE_BEHAVIOR
        self.set_cache_behavior(cache_behavior)

    def setp(self, allow_overriding: bool = None, cache_behavior: CacheBehavior = None, **kwargs):
        """
        Configure a quib with certain attributes- because this function is expected to be used by users, we never
        setattr to anything before checking the types.
        """
        super(FunctionQuib, self).setp(allow_overriding, **kwargs)
        if cache_behavior is not None:
            self.set_cache_behavior(cache_behavior)
        return self

    @cached_property
    def parents(self) -> Set[Quib]:
        return set(iter_quibs_in_args(self.args, self.kwargs))

    @classmethod
    def create(cls, func, func_args=(), func_kwargs=None, cache_behavior=None, evaluate_now=False, **init_kwargs):
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
                   cache_behavior=cache_behavior, **init_kwargs)
        for arg in iter_quibs_in_args(func_args, func_kwargs):
            arg.add_child(self)

        if evaluate_now:
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
    def _wrapper_call(cls, func, args, kwargs, **create_kwargs):
        """
        The actual code that runs when a quib-supporting function wrapper is called.
        """
        if is_there_a_quib_in_args(args, kwargs):
            return cls.create(func, args, kwargs, **create_kwargs)

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
        @raise_quib_call_exceptions_as_own
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
        When there are no override options, CannotChangeQuibAtPathException is raised.
        """
        get_override_group_for_change(AssignmentToQuib(self, assignment)).apply()

    def __repr__(self):
        if PRETTY_REPR:
            return self.pretty_repr()
        return f"<{self.__class__.__name__} - {getattr(self.func, '__name__', repr(self.func))}>"

    def _get_inner_functional_representation_expression(self) -> Union[MathExpression, str]:
        from pyquibbler.quib.function_quibs.pretty_converters import pretty_convert
        return pretty_convert.get_pretty_value_of_func_with_args_and_kwargs(self.func, self.args, self.kwargs)

    def get_cache_behavior(self):
        return self._cache_behavior

    @validate_user_input(cache_behavior=(str, CacheBehavior))
    def set_cache_behavior(self, cache_behavior: CacheBehavior):
        if isinstance(cache_behavior, str):
            try:
                cache_behavior = CacheBehavior[cache_behavior.upper()]
            except KeyError:
                raise UnknownCacheBehaviorException(cache_behavior)
        self._cache_behavior = cache_behavior

    def _backwards_translate_path(self, path: List[PathComponent]) -> Dict[Quib, str]:
        """
        Get a mapping of argument data source quibs to their respective paths that influenced the given path (`path`)
        """
        return {}

    def _replace_sub_argument_with_value(self, quibs_to_paths, inner_arg: Union[Quib, Any]):
        """
        Replace an argument, potentially a quib, with it's relevant value, given a map of quibs_to_paths, which
        describes for each quib what path it needs to be valid at
        """
        if isinstance(inner_arg, QuibRef):
            return inner_arg.quib

        if isinstance(inner_arg, Quib):
            if inner_arg in quibs_to_paths:
                path = quibs_to_paths[inner_arg]
            elif self._is_quib_a_data_source(inner_arg):
                # If the quib is a data source, and we didn't see it in the result, we don't need it to be valid at any
                # paths (it did not appear in quibs_to_paths)
                path = None
            else:
                # This is a paramater quib- we always need a parameter quib to be completely valid regardless of where
                # we need ourselves (this quib) to be valid
                path = []

            return inner_arg.get_value_valid_at_path(path)

        return inner_arg

    def _prepare_args_for_call(self, valid_path: Optional[List[PathComponent]]):
        """
        Prepare arguments to call self.func with - replace quibs with values valid at the given path,
        and QuibRefs with quibs.
        """
        quibs_to_paths = {} if valid_path is None else self._backwards_translate_path(valid_path)
        replace_func = functools.partial(self._replace_sub_argument_with_value, quibs_to_paths)
        new_args = [recursively_run_func_on_object(replace_func, arg) for arg in self.args]
        new_kwargs = {key: recursively_run_func_on_object(replace_func, val) for key, val in self.kwargs.items()}
        return new_args, new_kwargs

    def _call_func(self, valid_path: Optional[List[PathComponent]]):
        """
        Call the function wrapped by this FunctionQuib with the
        given arguments after replacing quib with their values.

        The result should be valid at valid_path- the default implementation is to always get a result that's value
        for all paths (not diverged), which will necessarily be also valid at `valid_path`.
        This function can and should be overriden if there is a more specific implementation for getting a value only
        valid at valid_path
        """
        new_args, new_kwargs = self._prepare_args_for_call(valid_path)
        with external_call_failed_exception_handling():
            return self.func(*new_args, **new_kwargs)

    def _forward_translate_path(self, invalidator_quib: Quib, path: List[PathComponent]) -> List[List[PathComponent]]:
        """
        Forward and translate the invalidation path in order to get a list of paths
        """
        return [[]]

    def _get_data_source_quibs(self) -> Set:
        """
        Get all the data source quib parents of this function quib
        """
        return set()

    def _is_quib_a_data_source(self, quib: Quib):
        """
        Returns whether this quib is considered a data source or not. This defaults to false, as a parameter (our
        current other option) is unknown in what it does to the result.
        """
        return quib in self._get_data_source_quibs()

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        """
        Get all the paths for invalidation of children
        """
        if len(path) == 0 or not self._is_quib_a_data_source(invalidator_quib):
            # We want to completely invalidate our children
            # if either a parameter changed or a data quib changed completely (at entire path)
            return [[]]
        return self._forward_translate_path(invalidator_quib, path)

    @lru_cache()
    def get_args_values(self, include_defaults=True):
        return ArgsValues.from_function_call(self.func, self.args, self.kwargs, include_defaults)

    @property
    def _save_directory(self) -> pathlib.Path:
        return self.project.function_quib_directory
