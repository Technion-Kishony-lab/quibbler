from __future__ import annotations

import functools
import os
import pathlib
import pickle
import types

import numpy as np
from functools import cached_property
from operator import getitem
from typing import Set, Any, TYPE_CHECKING, Optional, Tuple, Type, List, Callable, Dict, Union, Iterable, Mapping
from weakref import WeakSet
from contextlib import contextmanager

from matplotlib.widgets import AxesWidget

from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.quib import get_override_group_for_change
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.quib.graphics.graphics_function_quib import create_array_from_func
from pyquibbler.quib.quib_guard import add_new_quib_to_guard_if_exists, guard_get_value, QuibGuard
from pyquibbler.quib.assignment.assignment_template import InvalidTypeException, create_assignment_template
from pyquibbler.quib.assignment.utils import FailedToDeepAssignException
from pyquibbler.quib.function_quibs.external_call_failed_exception_handling import raise_quib_call_exceptions_as_own, \
    add_quib_to_fail_trace_if_raises_quib_call_exception, external_call_failed_exception_handling
from pyquibbler.quib.override_choice import OverrideRemoval
from pyquibbler.quib.assignment import AssignmentTemplate, Overrider, Assignment, \
    AssignmentToQuib
from pyquibbler.quib.function_quibs.cache import create_cache
from pyquibbler.quib.function_quibs.cache.shallow.indexable_cache import transform_cache_to_nd_if_necessary_given_path
from pyquibbler.quib.refactor.cache_behavior import CacheBehavior
from pyquibbler.quib.refactor.exceptions import OverridingNotAllowedException, UnknownUpdateTypeException
from pyquibbler.quib.refactor.graphics import UpdateType
from pyquibbler.quib.refactor.iterators import iter_quibs_in_args
from pyquibbler.quib.refactor.method_caching import cache_method_until_full_invalidation
from pyquibbler.quib.refactor.repr.pretty_converters import MathExpression
from pyquibbler.quib.refactor.repr.repr_mixin import ReprMixin
from pyquibbler.quib.utils import quib_method, Unpacker, recursively_run_func_on_object, \
    deep_copy_without_quibs_or_graphics, QuibRef
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.env import LEN_RAISE_EXCEPTION, GET_VARIABLE_NAMES, SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.input_validation_utils import validate_user_input, InvalidArgumentException
from pyquibbler.logger import logger
from pyquibbler.project import Project

if TYPE_CHECKING:
    from pyquibbler.quib.graphics import GraphicsFunctionQuib
    from pyquibbler.quib.override_choice import ChoiceContext, OverrideChoice


def get_user_friendly_name_for_requested_valid_path(valid_path: Optional[List[PathComponent]]):
    """
    Get a user-friendly name representing the call to get_value_valid_at_path
    """
    if valid_path is None:
        return 'get_blank_value()'
    elif len(valid_path) == 0:
        return 'get_value()'
    else:
        return f'get_value_valid_at_path({valid_path})'


class Quib(ReprMixin):
    """
    An abstract class to describe the common methods and attributes of all quib types.
    """
    _IS_WITHIN_GET_VALUE_CONTEXT = False

    def __init__(self, func: Callable,
                 args: Tuple[Any, ...],
                 kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior],
                 assignment_template: AssignmentTemplate,
                 allow_overriding: bool,
                 is_known_graphics_func: bool,
                 name: Optional[str],
                 file_name: Optional[str],
                 line_no: Optional[str]):
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._cache_behavior = cache_behavior
        self._assignment_template = assignment_template
        self._is_known_graphics_func = is_known_graphics_func
        self._cache = None
        self._name = name
        self._graphics_collections: Optional[np.array] = None

        self._children = WeakSet()
        self._overrider = Overrider()
        # TODO: For iquibs this needs to be true
        self._allow_overriding = allow_overriding
        self.method_cache = {}
        self._quibs_allowed_to_assign_to = None
        self._override_choice_cache = {}
        self.created_in_get_value_context = self._IS_WITHIN_GET_VALUE_CONTEXT
        self.file_name = file_name
        self.line_no = line_no
        self._redraw_update_type = UpdateType.DRAG

        # TODO: Move to factory
        self.project.register_quib(self)
        self._user_defined_save_directory = None
        add_new_quib_to_guard_if_exists(self)

    @property
    def func(self):
        return self._func

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs

    @property
    def func_creates_graphics(self):
        return self._is_known_graphics_func or self._did_create_graphics

    @property
    def _did_create_graphics(self) -> bool:
        return any(graphics_collection.artists for graphics_collection in self._flat_graphics_collections())

    @property
    def cache_status(self):
        """
        User interface to check cache validity.
        """
        return self._cache.get_cache_status() if self._cache is not None else CacheStatus.ALL_INVALID

    def get_axeses(self):
        return []

    def redraw_if_appropriate(self):
        """
        Redraws the quib if it's appropriate
        """
        from pyquibbler.quib.refactor.graphics import is_within_drag
        if self._redraw_update_type in [UpdateType.NEVER, UpdateType.CENTRAL] \
                or (self._redraw_update_type == UpdateType.DROP and is_within_drag()):
            return

        return self.get_value()

    def _flat_graphics_collections(self):
        return list(self._graphics_collections.flat) if self._graphics_collections else []

    @property
    def project(self) -> Project:
        return Project.get_or_create()

    def setp(self, allow_overriding: bool = None, assignment_template=None,
             save_directory: Union[str, pathlib.Path] = None,
             **kwargs):
        """
        Configure a quib with certain attributes- because this function is expected to be used by users, we never
        setattr to anything before checking the types.
        """
        if allow_overriding is not None:
            self.set_allow_overriding(allow_overriding)
        if assignment_template is not None:
            self.set_assignment_template(assignment_template)
        if save_directory is not None:
            self.set_save_directory(save_directory)
        if 'name' in kwargs:
            self.set_name(kwargs.pop('name'))
        return self

    @validate_user_input(update_type=(str, UpdateType))
    def set_redraw_update_type(self, update_type: Union[str, UpdateType]):
        """
        Set when to redraw a quib- on "drag", on "drop", on "central" refresh, or "never" (see UpdateType enum)
        """
        if isinstance(update_type, str):
            try:
                update_type = UpdateType[update_type.upper()]
            except KeyError:
                raise UnknownUpdateTypeException(update_type)
        self._redraw_update_type = update_type

    @validate_user_input(allow_overriding=bool)
    def set_allow_overriding(self, allow_overriding: bool):
        """
        Set whether the quib can be overridden- this defaults to True in iquibs and False in function quibs
        """
        self._allow_overriding = allow_overriding

    @property
    def children(self) -> Set[Quib]:
        """
        Return a copy of the current children weakset.
        """
        # We return a copy of the set because self._children can change size during iteration
        return set(self._children)

    def store_override_choice(self, context: ChoiceContext, choice: OverrideChoice) -> None:
        """
        Store a user override choice in the cache for future use.
        """
        self._override_choice_cache[context] = choice

    def try_load_override_choice(self, context: ChoiceContext) -> Optional[OverrideChoice]:
        """
        If a choice fitting the current options has been cached, return it. Otherwise return None.
        """
        return self._override_choice_cache.get(context)

    def _get_children_recursively(self) -> Set[Quib]:
        children = self.children
        for child in self.children:
            children |= child._get_children_recursively()
        return children

    def _get_graphics_function_quibs_recursively(self) -> Set[Quib]:
        """
        Get all artists that directly or indirectly depend on this quib.
        """
        return {child for child in self._get_children_recursively() if child.func_creates_graphics}

    def _redraw(self) -> None:
        """
        Redraw all artists that directly or indirectly depend on this quib.
        """
        from pyquibbler.quib.refactor.graphics.redraw import redraw_quibs_with_graphics_or_add_in_aggregate_mode
        quibs = self._get_graphics_function_quibs_recursively()
        redraw_quibs_with_graphics_or_add_in_aggregate_mode(quibs)

    def set_assigned_quibs(self, quibs: Optional[Iterable[Quib]]) -> None:
        """
        Set the quibs to which assignments to this quib could translate to overrides in.
        When None is given, a dialog will be used to choose between options.
        """
        self._quibs_allowed_to_assign_to = quibs if quibs is None else set(quibs)

    def allows_assignment_to(self, quib: Quib) -> bool:
        """
        Returns True if this quib allows assignments to it to be translated into assignments to the given quib,
        and False otherwise.
        """
        return True if self._quibs_allowed_to_assign_to is None else quib in self._quibs_allowed_to_assign_to

    def invalidate_and_redraw_at_path(self, path: Optional[List[PathComponent]] = None) -> None:
        """
        Perform all actions needed after the quib was mutated (whether by overriding or inverse assignment).
        If path is not given, the whole quib is invalidated.
        """
        from pyquibbler import timer
        if path is None:
            path = []

        with timer("quib_invalidation", lambda x: logger.info(f"invalidation {x}")):
            self._invalidate_children_at_path(path)
        self._redraw()

    def _invalidate_children_at_path(self, path: List[PathComponent]) -> None:
        """
        Change this quib's state according to a change in a dependency.
        """
        for child in self.children:
            child._invalidate_quib_with_children_at_path(self, path)

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: List[PathComponent]) -> List[Optional[List[PathComponent]]]:
        """
        Get the new paths for invalidating children- a quib overrides this method if it has a specific way to translate
        paths to new invalidation paths.
        If not, invalidate all children all over; as you have no more specific way to invalidate them
        """
        return [[]]

    def _on_type_change(self):
        self.method_cache.clear()

    def _invalidate_self(self, path: List[PathComponent]):
        """
        This method is called whenever a quib itself is invalidated; subclasses will override this with their
        implementations for invalidations.
        For example, a simple implementation for a quib which is a function could be setting a boolean to true or
        false signifying validity
        """

    def _get_loop_shape(self) -> Tuple[int, ...]:
        return ()

    @staticmethod
    def _apply_assignment_to_cache(original_value, cache, assignment):
        """
        Apply an assignment to a cache, setting valid if it was an assignment and invalid if it was an assignmentremoval
        """
        cache = transform_cache_to_nd_if_necessary_given_path(cache, assignment.path)
        try:
            if isinstance(assignment, Assignment):
                # Our cache only accepts shallow paths, so any validation to a non-shallow path is not necessarily
                # overridden at the first component completely- so we ignore it
                if len(assignment.path) <= 1:
                    cache.set_valid_value_at_path(assignment.path, assignment.value)
            else:
                # Our cache only accepts shallow paths, so we need to consider any invalidation to a path deeper
                # than one component as an invalidation to the entire first component of that path
                if len(assignment.path) == 0:
                    cache = create_cache(original_value)
                else:
                    cache.set_invalid_at_path(assignment.path[:1])

        except (IndexError, TypeError):
            # it's very possible there's an old assignment that doesn't match our new "shape" (not specifically np)-
            # if so we don't care about it
            pass

        return cache

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

    def _is_quib_a_data_source(self, quib):
        return False

    def _is_completely_overridden_at_first_component(self, path) -> bool:
        """
        Get a list of all the non overridden paths (at the first component)
        """
        path = path[:1]
        assignments = list(self._overrider)
        if assignments:
            original_value = self._get_inner_value_valid_at_path(None)
            cache = create_cache(original_value)
            cache = transform_cache_to_nd_if_necessary_given_path(cache, path)
            for assignment in assignments:
                cache = self._apply_assignment_to_cache(original_value, cache, assignment)
            return len(cache.get_uncached_paths(path)) == 0
        return False

    def _invalidate_quib_with_children_at_path(self, invalidator_quib, path: List[PathComponent]):
        """
        Invalidate a quib and it's children at a given path.
        This method should be overriden if there is any 'special' implementation for either invalidating oneself
        or for translating a path for invalidation
        """
        new_paths = self._get_paths_for_children_invalidation(invalidator_quib, path)
        for new_path in new_paths:
            if new_path is not None:
                self._invalidate_self(new_path)
                if len(path) == 0 or not self._is_completely_overridden_at_first_component(new_path):
                    self._invalidate_children_at_path(new_path)

    def add_child(self, quib: Quib) -> None:
        """
        Add the given quib to the list of quibs that are dependent on this quib.
        """
        self._children.add(quib)

    def __len__(self):
        if LEN_RAISE_EXCEPTION:
            raise TypeError('len(Q), where Q is a quib, is not allowed. '
                            'To get a functional quib, use q(len,Q). '
                            'To get the len of the current value of Q, use len(Q.get_value()).')
        else:
            return len(self.get_value_valid_at_path(None))

    def __iter__(self):
        raise TypeError('Cannot iterate over quibs, as their size can vary. '
                        'Try Quib.iter_first() to iterate over the n-first items of the quib.')

    def override(self, assignment: Assignment, allow_overriding_from_now_on=True):
        """
        Overrides a part of the data the quib represents.
        """
        if allow_overriding_from_now_on:
            self._allow_overriding = True
        if not self._allow_overriding:
            raise OverridingNotAllowedException(self, assignment)
        self._overrider.add_assignment(assignment)
        if len(assignment.path) == 0:
            self._on_type_change()

        try:
            self.invalidate_and_redraw_at_path(assignment.path)
        except FailedToDeepAssignException as e:
            raise FailedToDeepAssignException(exception=e.exception, path=e.path) from None
        except InvalidTypeException as e:
            raise InvalidTypeException(e.type_) from None

        from pyquibbler.quib.graphics.widgets import is_within_drag
        if not is_within_drag():
            self.project.push_assignment_to_undo_stack(quib=self,
                                                       assignment=assignment,
                                                       index=len(list(self._overrider)) - 1,
                                                       overrider=self._overrider)

    def remove_override(self, path: List[PathComponent], invalidate_and_redraw: bool = True):
        """
        Remove overriding in a specific path in the quib.
        """
        assignment_removal = self._overrider.remove_assignment(path)
        if assignment_removal is not None:
            self.project.push_assignment_to_undo_stack(assignment=assignment_removal,
                                                       index=len(list(self._overrider)) - 1,
                                                       overrider=self._overrider,
                                                       quib=self)
        if len(path) == 0:
            self._on_type_change()
        if invalidate_and_redraw:
            self.invalidate_and_redraw_at_path(path=path)

    def assign(self, assignment: Assignment) -> None:
        """
        Create an assignment with an Assignment object, overriding the current values at the assignment's paths with the
        assignment's value
        """
        get_override_group_for_change(AssignmentToQuib(self, assignment)).apply()

    @raise_quib_call_exceptions_as_own
    def assign_value(self, value: Any) -> None:
        """
        Helper method to assign a single value and override the whole value of the quib
        """
        self.assign(Assignment(value=value, path=[]))

    @raise_quib_call_exceptions_as_own
    def assign_value_to_key(self, key: Any, value: Any) -> None:
        """
        Helper method to assign a value at a specific key
        """
        from ..assignment.assignment import PathComponent
        self.assign(Assignment(path=[PathComponent(component=key, indexed_cls=self.get_type())], value=value))

    def __getitem__(self, item):
        # We don't use the normal operator_overriding interface for two reasons:
        # 1. It can create issues with hinting in IDEs (for example, Pycharm will not recognize that Quibs have a
        # getitem and will issue a warning)
        # 2. We need the function to not be created dynamically as it needs to be in the inverser's supported functions
        # in order to be inversed correctly (and not simply override)
        from pyquibbler.quib.refactor.factory import create_quib
        return create_quib(func=getitem, args=[self, item])

    def __setitem__(self, key, value):
        from ..assignment.assignment import PathComponent
        if isinstance(key, Quib):
            key = key.get_value()
        self.assign(Assignment(value=value, path=[PathComponent(component=key, indexed_cls=self.get_type())]))

    @validate_user_input(name=(str, type(None)))
    def set_name(self, name: Optional[str]):
        """
        Set the quib's name- this will override any name automatically created if it exists.
        """
        if name is None or name.isidentifier():
            self._name = name
        else:
            raise ValueError('name must be None or a valid alphanumeic python identifier')

    @property
    def name(self) -> Optional[str]:
        """
        Get the name of the quib- this can either be an automatic name if created (the var name), a given name if given,
        and None if neither
        """
        return self._name

    @property
    def allow_overriding(self) -> bool:
        return self._allow_overriding

    def get_assignment_template(self) -> AssignmentTemplate:
        return self._assignment_template

    def set_assignment_template(self, *args) -> None:
        """
        Sets an assignment template for the quib.
        Usage:

        - quib.set_assignment_template(assignment_template): set a specific AssignmentTemplate object.
        - quib.set_assignment_template(min, max): set the template to a bound template between min and max.
        - quib.set_assignment_template(start, stop, step): set the template to a bound template between min and max.
        """
        self._assignment_template = create_assignment_template(args)

    def _backwards_translate_path(self, valid_path: List[PathComponent]):
        return []

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

    def _initialize_graphics_collections(self):
        """
        Initialize the array representing all the graphics_collection objects for all iterations of the function
        """
        loop_shape = self._get_loop_shape()
        if self._graphics_collections is not None and self._graphics_collections.shape != loop_shape:
            for graphics_collection in self._flat_graphics_collections():
                graphics_collection.remove_artists()
            self._graphics_collections = None
        if self._graphics_collections is None:
            self._graphics_collections = create_array_from_func(GraphicsCollection, loop_shape)

    def _call_func(self, valid_path: List[PathComponent]):
        self._initialize_graphics_collections()

        # TODO: how do we choose correct indexes for graphics collection?
        graphics_collection: GraphicsCollection = self._graphics_collections[()]

        # TODO: pass_quibs
        # TODO: quib_guard

        with graphics_collection.track_and_handle_new_graphics(kwargs_specified_in_artists_creation=set(self.kwargs.keys())):
            new_args, new_kwargs = self._prepare_args_for_call(valid_path)
            with external_call_failed_exception_handling():
                res = self.func(*new_args, **new_kwargs)

                # TODO: Move this logic somewhere else
                if len(graphics_collection.widgets) > 0 and isinstance(res, AxesWidget):
                    assert len(graphics_collection.widgets) == 1
                    res = list(graphics_collection.widgets)[0]

                # We don't allow returning quibs as results from functions
                from pyquibbler.quib import Quib
                if isinstance(res, Quib):
                    res = res.get_value()
                ####

                return res

    @raise_quib_call_exceptions_as_own
    def get_value_valid_at_path(self, path: Optional[List[PathComponent]]) -> Any:
        """
        Get the actual data that this quib represents, valid at the path given in the argument.
        The value will necessarily return in the shape of the actual result, but only the values at the given path
        are guaranteed to be valid
        """
        guard_get_value(self)
        name_for_call = get_user_friendly_name_for_requested_valid_path(path)
        with add_quib_to_fail_trace_if_raises_quib_call_exception(self, name_for_call, False):
            inner_value = self._call_func(path)

        # TODO: change to create_cache etc
        self._cache = create_cache(inner_value)

        return self._overrider.override(inner_value, self._assignment_template)

    @staticmethod
    @contextmanager
    def _get_value_context():
        """
        Change cls._IS_WITHIN_GET_VALUE_CONTEXT while in the process of running get_value.
        This has to be a static method as the _IS_WITHIN_GET_VALUE_CONTEXT is a global state for all quib types
        """
        if Quib._IS_WITHIN_GET_VALUE_CONTEXT:
            yield
        else:
            Quib._IS_WITHIN_GET_VALUE_CONTEXT = True
            try:
                yield
            finally:
                Quib._IS_WITHIN_GET_VALUE_CONTEXT = False

    @raise_quib_call_exceptions_as_own
    def get_value(self) -> Any:
        """
        Get the entire actual data that this quib represents, all valid.
        This function might perform several different computations - function quibs
        are lazy, so a function quib might need to calculate uncached values and might
        even have to calculate the values of its dependencies.
        """
        with self._get_value_context():
            return self.get_value_valid_at_path([])

    def get_override_list(self) -> Overrider:
        """
        Returns an Overrider object representing a list of overrides performed on the quib.
        """
        return self._overrider

    # We cache the type, so quibs without cache will still remember their types.
    @cache_method_until_full_invalidation
    def get_type(self) -> Type:
        """
        Get the type of wrapped value.
        """
        with add_quib_to_fail_trace_if_raises_quib_call_exception(quib=self, call='get_type()', replace_last=True):
            return type(self.get_value_valid_at_path(None))

    # We cache the shape, so quibs without cache will still remember their shape.
    @cache_method_until_full_invalidation
    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        with add_quib_to_fail_trace_if_raises_quib_call_exception(quib=self, call='get_shape()', replace_last=True):
            res = self.get_value_valid_at_path(None)

        try:
            return np.shape(res)
        except ValueError:
            if hasattr(res, '__len__'):
                return len(res),
            raise

    @cache_method_until_full_invalidation
    def get_ndim(self) -> int:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        with add_quib_to_fail_trace_if_raises_quib_call_exception(quib=self, call='get_ndim()', replace_last=True):
            res = self.get_value_valid_at_path(None)

        try:
            return np.ndim(res)
        except ValueError:
            if hasattr(res, '__len__'):
                return 1
            raise

    @quib_method('elementwise')
    def get_override_mask(self):
        """
        Assuming this quib represents a numpy ndarray, return a quib representing its override mask.
        The override mask is a boolean array of the same shape, in which every value is
        set to True if the matching value in the array is overridden, and False otherwise.
        """
        if issubclass(self.get_type(), np.ndarray):
            mask = np.zeros(self.get_shape(), dtype=np.bool)
        else:
            mask = recursively_run_func_on_object(func=lambda x: False, obj=self.get_value())
        return self._overrider.fill_override_mask(mask)

    def iter_first(self, amount: Optional[int] = None):
        """
        Returns an iterator to the first `amount` elements of the quib.
        `a, b = quib.iter_first(2)` is the same as `a, b = quib[0], quib[1]`.
        When `amount` is not given, quibbler will try to detect the correct amount automatically, and
        might fail with a RuntimeError.
        For example, `a, b = iquib([1, 2]).iter_first()` is the same as `a, b = iquib([1, 2]).iter_first(2)`.
        But note that even if the quib is larger than the unpacked amount, the iterator will still yield only the first
        items - `a, b = iquib([1, 2, 3, 4]).iter_first()` is the same as `a, b = iquib([1, 2, 3, 4]).iter_first(2)`.
        """
        return Unpacker(self, amount)

    def remove_child(self, quib_to_remove: Quib):
        """
        Removes a child from the quib, no longer sending invalidations to it
        """
        self._children.remove(quib_to_remove)

    @property
    def parents(self) -> Set[Quib]:
        """
        Returns a list of quibs that this quib depends on.
        """
        return set(iter_quibs_in_args(self.args, self.kwargs))

    @cached_property
    def ancestors(self) -> Set[Quib]:
        """
        Return all ancestors of the quib, going recursively up the tree
        """
        ancestors = set()
        for parent in self.parents:
            ancestors.add(parent)
            ancestors |= parent.ancestors
        return ancestors

    def get_inversions_for_override_removal(self, override_removal: OverrideRemoval) -> List[OverrideRemoval]:
        """
        Get a list of overide removals to parent quibs which could be applied instead of the given override removal
        and produce the same change in the value of this quib.
        """
        return []

    def get_inversions_for_assignment(self, assignment: Assignment) -> List[AssignmentToQuib]:
        """
        Get a list of assignments to parent quibs which could be applied instead of the given assignment
        and produce the same change in the value of this quib.
        """
        return []

    @property
    def _default_save_directory(self) -> Optional[pathlib.Path]:
        pass

    @property
    def _save_path(self) -> Optional[pathlib.Path]:
        save_name = self.name if self.name else hash(self.functional_representation)
        return self._save_directory / f"{save_name}.quib" if self._default_save_directory else None

    @property
    def _save_directory(self):
        return self._user_defined_save_directory \
            if self._user_defined_save_directory is not None else self._default_save_directory

    @validate_user_input(path=(str, pathlib.Path))
    def set_save_directory(self, path: Union[str, pathlib.Path]):
        """
        Set the save path of the quib (where it will be loaded/saved)
        """
        if isinstance(path, str):
            path = pathlib.Path(path)
        self._user_defined_save_directory = path.resolve()

    def save_if_relevant(self):
        """
        Save the quib if relevant- this will NOT save if the quib does not have overrides, as there is nothing to save
        """
        os.makedirs(self._save_path.parent, exist_ok=True)
        if len(list(self._overrider)) > 0:
            with open(self._save_path, 'wb') as f:
                pickle.dump(self._overrider, f)

    def load(self):
        if self._save_path and os.path.exists(self._save_path):
            with open(self._save_path, 'rb') as f:
                self._overrider = pickle.load(f)
                self.invalidate_and_redraw_at_path([])
