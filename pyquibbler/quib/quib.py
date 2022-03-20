from __future__ import annotations

import copy
import functools
import pathlib
import pickle
import weakref
import warnings

import json_tricks
import numpy as np

from pyquibbler.quib.types import FileAndLineNumber
from pyquibbler.utilities.file_path import PathWithHyperLink
from functools import cached_property
from typing import Set, Any, TYPE_CHECKING, Optional, Tuple, Type, List, Union, Iterable, Mapping, Callable
from weakref import WeakSet

from matplotlib.artist import Artist

from pyquibbler.env import LEN_RAISE_EXCEPTION, PRETTY_REPR, REPR_RETURNS_SHORT_NAME, REPR_WITH_OVERRIDES
from pyquibbler.graphics import is_within_drag
from pyquibbler.quib.quib_guard import guard_raise_if_not_allowed_access_to_quib, \
    CannotAccessQuibInScopeException
from pyquibbler.quib.pretty_converters import MathExpression, FailedMathExpression, \
    NameMathExpression, pretty_convert
from pyquibbler.quib.utils.miscellaneous import copy_and_replace_quibs_with_vals, NoValue
from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation_with_sources_metadata, \
    get_func_call_for_translation_without_sources_metadata
from pyquibbler.utilities.input_validation_utils import validate_user_input, InvalidArgumentValueException, \
    get_enum_by_str
from pyquibbler.utilities.iterators import recursively_run_func_on_object, recursively_compare_objects_type, \
    recursively_cast_one_object_by_other
from pyquibbler.utilities.unpacker import Unpacker
from pyquibbler.logger import logger
from pyquibbler.project import Project
from pyquibbler.inversion.exceptions import NoInvertersFoundException
from pyquibbler.path import FailedToDeepAssignException, PathComponent, Path, Paths
from pyquibbler.assignment import InvalidTypeException, OverrideRemoval, get_override_group_for_change, \
    AssignmentTemplate, Overrider, Assignment, AssignmentToQuib, create_assignment_template
from pyquibbler.quib.func_calling.cache_behavior import CacheBehavior
from pyquibbler.quib.exceptions import OverridingNotAllowedException, UnknownUpdateTypeException, \
    InvalidCacheBehaviorForQuibException
from pyquibbler.quib.external_call_failed_exception_handling import raise_quib_call_exceptions_as_own
from pyquibbler.quib.graphics import UpdateType
from pyquibbler.translation.translate import forwards_translate, NoTranslatorsFoundException, \
    backwards_translate
from pyquibbler.cache import create_cache, CacheStatus
from pyquibbler.file_syncing import SaveFormat, SAVE_FORMAT_TO_FILE_EXT, CannotSaveFunctionQuibsAsValueException, \
    ResponseToFileNotDefined, FileNotDefinedException, QuibFileSyncer, SAVE_FORMAT_TO_FQUIB_SAVE_FORMAT, \
    FIRST_LINE_OF_FORMATTED_TXT_FILE
from pyquibbler.quib.get_value_context_manager import get_value_context, is_within_get_value_context

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition
    from pyquibbler.assignment.override_choice import ChoiceContext
    from pyquibbler.assignment import OverrideChoice
    from pyquibbler.quib.func_calling import QuibFuncCall


class QuibHandler:
    """
    takes care of all the functionality of a quib.
    allows the Quib class to only have user functions
    All data is stored on the QuibHandler (the Quib itself is state-less)
    """

    def __init__(self, quib: Quib, quib_function_call: QuibFuncCall,
                 assignment_template: Optional[AssignmentTemplate],
                 allow_overriding: bool,
                 assigned_name: Optional[str],
                 file_name: Optional[str],
                 line_no: Optional[str],
                 graphics_update_type: Optional[UpdateType],
                 save_directory: pathlib.Path,
                 save_format: Optional[SaveFormat],
                 can_contain_graphics: bool,
                 ):

        quib_weakref = weakref.ref(quib)
        self._quib_weakref = quib_weakref
        self._override_choice_cache = {}
        self.quib_function_call = quib_function_call

        self.assignment_template = assignment_template
        self.assigned_name = assigned_name

        self.children = WeakSet()
        self._overrider: Optional[Overrider] = None
        self.file_syncer: QuibFileSyncer = QuibFileSyncer(quib_weakref)
        self.allow_overriding = allow_overriding
        self.assigned_quibs = None
        self.created_in_get_value_context = is_within_get_value_context()
        self.created_in: Optional[FileAndLineNumber] = \
            FileAndLineNumber(file_name, line_no) if file_name else None
        self.graphics_update_type = graphics_update_type

        self.save_directory = save_directory

        self.save_format = save_format
        self.can_contain_graphics = can_contain_graphics

        from pyquibbler.quib.graphics.persist import persist_artists_on_quib_weak_ref
        self.quib_function_call.artists_creation_callback = functools.partial(persist_artists_on_quib_weak_ref,
                                                                              weakref.ref(quib))

    """
    relationships
    """

    @property
    def quib(self):
        return self._quib_weakref()

    @property
    def project(self) -> Project:
        return Project.get_or_create()

    def add_child(self, quib: Quib) -> None:
        """
        Add the given quib to the list of quibs that are dependent on this quib.
        """
        self.children.add(quib)

    def remove_child(self, quib_to_remove: Quib):
        """
        Removes a child from the quib, no longer sending invalidations to it
        """
        self.children.remove(quib_to_remove)

    """
    graphics
    """

    def redraw_if_appropriate(self):
        """
        Redraws the quib if it's appropriate
        """
        if self.graphics_update_type in [UpdateType.NEVER, UpdateType.CENTRAL] \
                or (self.graphics_update_type == UpdateType.DROP and is_within_drag()):
            return

        return self.quib.get_value()

    def _iter_artist_lists(self) -> Iterable[List[Artist]]:
        return map(lambda g: g.artists, self.quib_function_call.flat_graphics_collections())

    def _iter_artists(self) -> Iterable[Artist]:
        return (artist for artists in self._iter_artist_lists() for artist in artists)

    def get_axeses(self):
        return {artist.axes for artist in self._iter_artists()}

    def _redraw(self) -> None:
        """
        Redraw all artists that directly or indirectly depend on this quib.
        """
        from pyquibbler.quib.graphics.redraw import redraw_quibs_with_graphics_or_add_in_aggregate_mode
        quibs = self._get_descendant_graphics_quibs_recursively()
        redraw_quibs_with_graphics_or_add_in_aggregate_mode(quibs)

    def _get_descendant_graphics_quibs_recursively(self) -> Set[Quib]:
        """
        Get all artists that directly or indirectly depend on this quib.
        """
        return {child for child in self.quib.get_descendants() if child.is_graphics_quib}

    """
    Invalidation
    """

    def invalidate_self(self, path: Path):
        """
        This method is called whenever a quib itself is invalidated; subclasses will override this with their
        implementations for invalidations.
        For example, a simple implementation for a quib which is a function could be setting a boolean to true or
        false signifying validity
        """
        if len(path) == 0:
            self.quib_function_call.on_type_change()
            self.quib_function_call.reset_cache()

        self.quib_function_call.invalidate_cache_at_path(path)

    def invalidate_and_redraw_at_path(self, path: Optional[Path] = None) -> None:
        """
        Perform all actions needed after the quib was mutated (whether by function_definitions or inverse assignment).
        If path is not given, the whole quib is invalidated.
        """
        from pyquibbler import timer
        if path is None:
            path = []

        with timer("quib_invalidation", lambda x: logger.info(f"invalidate {x}")):
            self._invalidate_children_at_path(path)

        self._redraw()

    def _invalidate_children_at_path(self, path: Path) -> None:
        """
        Change this quib's state according to a change in a dependency.
        """
        for child in set(self.children):  # We copy of the set because children can change size during iteration

            child.handler._invalidate_quib_with_children_at_path(self.quib, path)

    def _invalidate_quib_with_children_at_path(self, invalidator_quib: Quib, path: Path):
        """
        Invalidate a quib and it's children at a given path.
        This method should be overriden if there is any 'special' implementation for either invalidating oneself
        or for translating a path for invalidation
        """
        new_paths = self._get_paths_for_children_invalidation(invalidator_quib, path)
        for new_path in new_paths:
            if new_path is not None:
                self.invalidate_self(new_path)
                if len(path) == 0 or len(self._get_list_of_not_overridden_paths_at_first_component(new_path)) > 0:
                    self._invalidate_children_at_path(new_path)

    def _forward_translate_without_retrieving_metadata(self, invalidator_quib: Quib, path: Path) -> Paths:
        func_call, sources_to_quibs = get_func_call_for_translation_without_sources_metadata(
            self.quib_function_call
        )
        quibs_to_sources = {quib: source for source, quib in sources_to_quibs.items()}
        sources_to_forwarded_paths = forwards_translate(
            func_call=func_call,
            sources_to_paths={
                quibs_to_sources[invalidator_quib]: path
            },
        )
        return sources_to_forwarded_paths.get(quibs_to_sources[invalidator_quib], [])

    def _forward_translate_with_retrieving_metadata(self, invalidator_quib: Quib, path: Path) -> Paths:
        func_call, sources_to_quibs = get_func_call_for_translation_with_sources_metadata(
            self.quib_function_call
        )
        quibs_to_sources = {quib: source for source, quib in sources_to_quibs.items()}
        sources_to_forwarded_paths = forwards_translate(
            func_call=func_call,
            sources_to_paths={
                quibs_to_sources[invalidator_quib]: path
            },
            shape=self.quib.get_shape(),
            type_=self.quib.get_type(),
            **self.quib_function_call.get_result_metadata()
        )
        return sources_to_forwarded_paths.get(quibs_to_sources[invalidator_quib], [])

    def _forward_translate_source_path(self, invalidator_quib: Quib, path: Path) -> Paths:
        """
        Forward translate a path, first attempting to do it WITHOUT using getting the shape and type, and if/when
        failure does grace us, we attempt again with shape and type
        """
        try:
            return self._forward_translate_without_retrieving_metadata(invalidator_quib, path)
        except NoTranslatorsFoundException:
            try:
                return self._forward_translate_with_retrieving_metadata(invalidator_quib, path)
            except NoTranslatorsFoundException:
                return [[]]

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: Path) -> Paths:
        """
        Forward translate a path for invalidation, first attempting to do it WITHOUT using getting the shape and type,
        and if/when failure does grace us, we attempt again with shape and type.
        If we have no translators, we forward the path to invalidate all, as we have no more specific way to do it
        """
        # We always invalidate all if it's a parameter source quib
        if invalidator_quib not in self.quib_function_call.get_data_sources():
            return [[]]

        try:
            return self._forward_translate_without_retrieving_metadata(invalidator_quib, path)
        except NoTranslatorsFoundException:
            try:
                return self._forward_translate_with_retrieving_metadata(invalidator_quib, path)
            except NoTranslatorsFoundException:
                return [[]]

    """
    assignments
    """

    @property
    def overrider(self):
        if self._overrider is None:
            self._overrider = Overrider()
        return self._overrider

    @property
    def is_overridden(self):
        return self._overrider is not None and len(self._overrider)

    def _add_override(self, assignment: Assignment):
        self.overrider.add_assignment(assignment)
        if len(assignment.path) == 0:
            self.quib_function_call.on_type_change()

        try:
            self.invalidate_and_redraw_at_path(assignment.path)
        except FailedToDeepAssignException as e:
            raise FailedToDeepAssignException(exception=e.exception, path=e.path) from None
        except InvalidTypeException as e:
            raise InvalidTypeException(e.type_) from None

    def override(self, assignment: Assignment, allow_overriding_from_now_on=True):
        """
        Overrides a part of the data the quib represents.
        """
        if allow_overriding_from_now_on:
            self.allow_overriding = True
        if not self.allow_overriding:
            raise OverridingNotAllowedException(self.quib, assignment)

        self._add_override(assignment)

        if not is_within_drag():
            self.project.push_assignment_to_undo_stack(quib=self.quib,
                                                       assignment=assignment,
                                                       index=len(self.overrider) - 1,
                                                       overrider=self.overrider)
            self.file_syncer.on_data_changed()

    def remove_override(self, path: Path):
        """
        Remove function_definitions in a specific path in the quib.
        """
        assignment_removal = self.overrider.remove_assignment(path)
        if assignment_removal is not None and not is_within_drag():
            self.project.push_assignment_to_undo_stack(assignment=assignment_removal,
                                                       index=len(self.overrider) - 1,
                                                       overrider=self.overrider,
                                                       quib=self.quib)
            self.file_syncer.on_data_changed()
        if len(path) == 0:
            self.quib_function_call.on_type_change()
        self.invalidate_and_redraw_at_path(path=path)

    def apply_assignment(self, assignment: Assignment) -> None:
        """
        Create an assignment with an Assignment object,
        function_definitions the current values at the assignment's paths with the assignment's value
        """
        get_override_group_for_change(AssignmentToQuib(self.quib, assignment)).apply()

    def get_inversions_for_override_removal(self, override_removal: OverrideRemoval) -> List[OverrideRemoval]:
        """
        Get a list of overide removals to parent quibs which could be applied instead of the given override removal
        and produce the same change in the value of this quib.
        """
        from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation_with_sources_metadata
        func_call, sources_to_quibs = get_func_call_for_translation_with_sources_metadata(self.quib_function_call)
        try:
            sources_to_paths = backwards_translate(func_call=func_call, path=override_removal.path,
                                                   shape=self.quib.get_shape(), type_=self.quib.get_type())
        except NoTranslatorsFoundException:
            return []
        else:
            return [OverrideRemoval(sources_to_quibs[source], path) for source, path in sources_to_paths.items()]

    def get_inversions_for_assignment(self, assignment: Assignment) -> List[AssignmentToQuib]:
        """
        Get a list of assignments to parent quibs which could be applied instead of the given assignment
        and produce the same change in the value of this quib.
        """
        from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation_with_sources_metadata
        func_call, data_sources_to_quibs = get_func_call_for_translation_with_sources_metadata(self.quib_function_call)

        try:
            value = self.quib.get_value()
            # TODO: better implement with the line below. But need to take care of out-of-range assignments:
            # value = self.get_value_valid_at_path(assignment.path)

            from pyquibbler.inversion.invert import invert
            inversals = invert(func_call=func_call,
                               previous_result=value,
                               assignment=assignment)
        except NoInvertersFoundException:
            return []

        return [
            AssignmentToQuib(
                quib=data_sources_to_quibs[inversal.source],
                assignment=inversal.assignment
            )
            for inversal in inversals
        ]

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

    @staticmethod
    def _apply_assignment_to_cache(original_value, cache, assignment):
        """
        Apply an assignment to a cache, setting valid if it was an assignment and invalid if it was an assignmentremoval
        """
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

    def _get_list_of_not_overridden_paths_at_first_component(self, path) -> Paths:
        """
        Get a list of all the non overridden paths (at the first component)
        """
        path = path[:1]
        if not self.is_overridden:
            return [path]

        assignments = list(self.overrider)
        original_value = copy.deepcopy(self.get_value_valid_at_path(None))
        cache = create_cache(original_value)
        for assignment in assignments:
            cache = self._apply_assignment_to_cache(original_value, cache, assignment)
        return cache.get_uncached_paths(path)

    """
    get_value
    """

    def get_value_valid_at_path(self, path: Optional[Path]) -> Any:
        """
        Get the actual data that this quib represents, valid at the path given in the argument.
        The value will necessarily return in the shape of the actual result, but only the values at the given path
        are guaranteed to be valid
        """
        try:
            guard_raise_if_not_allowed_access_to_quib(self.quib)
        except CannotAccessQuibInScopeException:
            raise

        with get_value_context():
            if path is None:
                paths = [None]
            else:
                paths = self._get_list_of_not_overridden_paths_at_first_component(path)
            result = self.quib_function_call.run(paths)

        return self._overrider.override(result, self.assignment_template) if self.is_overridden \
            else result

    """
    file syncing
    """

    def on_project_directory_change(self):
        if not(self.save_directory is not None and self.save_directory.is_absolute()):
            self.file_syncer.on_file_name_changed()

    def on_file_name_change(self):
        self.file_syncer.on_file_name_changed()

    def save_assignments_or_value(self, file_path: pathlib.Path):
        save_format = self.quib.actual_save_format
        if save_format == SaveFormat.VALUE_TXT:
            self._save_value_as_txt(file_path)
        elif save_format == SaveFormat.VALUE_BIN:
            self._save_value_as_binary(file_path)
        elif save_format == SaveFormat.BIN:
            self.overrider.save_as_binary(file_path)
        elif save_format == SaveFormat.TXT:
            self.overrider.save_as_txt(file_path)

    def load_from_assignment_file_or_value_file(self, file_path: pathlib.Path):
        save_format = self.quib.actual_save_format
        if save_format == SaveFormat.VALUE_TXT:
            changed_paths = self._load_value_from_txt(file_path)
        elif save_format == SaveFormat.VALUE_BIN:
            changed_paths = self._load_value_from_binary(file_path)
        elif save_format == SaveFormat.BIN:
            changed_paths = self.overrider.load_from_binary(file_path)
        elif save_format == SaveFormat.TXT:
            changed_paths = self.overrider.load_from_txt(file_path)
        else:
            return

        self.project.clear_undo_and_redo_stacks()
        for path in changed_paths:
            self.invalidate_and_redraw_at_path(path)

    def clear_all_overrides(self):
        changed_paths = self.overrider.clear_assignments()

        self.project.clear_undo_and_redo_stacks()
        for path in changed_paths:
            self.invalidate_and_redraw_at_path(path)

    def _replace_value_after_load(self, value) -> Paths:
        self._add_override(Assignment(value=value, path=[]))
        self.project.clear_undo_and_redo_stacks()

        # TODO: check which specific elements changed.
        return [[]]

    def _save_value_as_binary(self, file_path):
        with open(file_path, 'wb') as f:
            pickle.dump(self.get_value_valid_at_path([]), f)

    def _load_value_from_binary(self, file) -> Paths:
        with open(file, 'rb') as f:
            return self._replace_value_after_load(pickle.load(f))

    def _save_value_as_txt(self, file_path: pathlib.Path):
        """
        Save an iquib value as a text file

        Note:
            * This method is only defined for iquibs.
            * The value must be of the same type as the original value of the iquib
            * Will fail with CannotSaveValueAsTextException if the iquib's value cannot be represented as text.
        """
        arg = self.quib_function_call.args[0]
        value = self.get_value_valid_at_path([])
        with open(file_path, 'w') as f:
            if not recursively_compare_objects_type(arg, value):
                f.write(FIRST_LINE_OF_FORMATTED_TXT_FILE + '\n\n')
                json_tricks.dump(value, f, primitives=False)
            else:
                json_tricks.dump(value, f, primitives=True)

    def _load_value_from_txt(self, file_path):
        """
        Load the quib value from the corresponding text file
        """

        with open(file_path, 'r') as f:
            is_formatted = f.readline() == FIRST_LINE_OF_FORMATTED_TXT_FILE + '\n'

        with open(file_path, 'r') as f:
            value = json_tricks.load(f)

        if not is_formatted:
            arg = self.quib_function_call.args[0]
            value = recursively_cast_one_object_by_other(arg, value)

        return self._replace_value_after_load(value)


class Quib:
    """
    A Quib is a node representing a singular call of a function with it's arguments (it's parents in the graph)
    """

    def __init__(self, quib_function_call: QuibFuncCall,
                 assignment_template: Optional[AssignmentTemplate],
                 allow_overriding: bool,
                 assigned_name: Optional[str],
                 file_name: Optional[str],
                 line_no: Optional[str],
                 graphics_update_type: Optional[UpdateType],
                 save_directory: pathlib.Path,
                 save_format: Optional[SaveFormat],
                 can_contain_graphics: bool,
                 ):

        self.handler = QuibHandler(self, quib_function_call,
                                   assignment_template,
                                   allow_overriding,
                                   assigned_name,
                                   file_name,
                                   line_no,
                                   graphics_update_type,
                                   save_directory,
                                   save_format,
                                   can_contain_graphics,
                                   )

    """
    Func metadata
    """

    @property
    def func(self) -> Callable:
        """
        The function run by the quib.

        A quib calls its function `func`, with the arguments `args` and the keyworded variables `kwargs`.
        The quib's value is gievn by:

        >>> value = func(*args, **kwargs)

        with any quibs in `args` or `kwargs` replaced by their values.

        Returns
        -------
        func : Callable, the called function

        See also
        --------
        args, kwargs

        Examples
        --------
        >>> w = iquib(0.5)
        >>> s = np.sin(w)
        >>> s.func
        np.sin
        """
        return self.handler.quib_function_call.func

    @property
    def args(self) -> List[Any]:
        """
        The arguments of the function run by the quib.

        A quib calls its function `func`, with the arguments `args` and the keyworded variables `kwargs`.
        The quib's value is gievn by:

        >>> value = func(*args, **kwargs)

        with any quibs in `args` or `kwargs` replaced by their values.

        `args` is a list of all positional arguments, which could be any object including other quibs.

        Returns
        -------
        args : list of Quib or any
            A list of arguments, which could be any object including other quibs.

        See also
        --------
        func, kwargs

        Examples
        --------
        >>> w = iquib(0.5)
        >>> s = w + 10
        >>> s.args
        [w, 10]
        """
        return self.handler.quib_function_call.args

    @property
    def kwargs(self) -> Mapping[str, Any]:
        """
        The keyworded arguments for the function run by the quib.

        A quib calls its function `func`, with the arguments `args` and the keyworded variables `kwargs`.
        The quib's value is gievn by:

        >>> value = func(*args, **kwargs)

        with any quibs in `args` or `kwargs` replaced by their values.

        `kwargs` is a dictionary of str keywords mapped to any object including non-quib or quib arguments.

        Returns
        -------
        kwargs : dict of str: any
            A dict of keyworded arguments, which could be any object including other quibs.

        See also
        --------
        func, args

        Examples
        --------
        >>> a = iquib(10)
        >>> s = np.linspace(start=0, stop=a)
        >>> s.kwargs
        {'start': 0, 'stop': a}
        """
        return self.handler.quib_function_call.kwargs

    @property
    def func_definition(self) -> FuncDefinition:
        """
        Properties of the function run by the quib.

        Returns
        -------
        func_definition : FuncDefinition
            An object containg the properties of the function.
        """
        from pyquibbler.function_definitions import get_definition_for_function
        return get_definition_for_function(self.func)

    @property
    def is_impure_func(self) -> bool:
        """
        Indicates whether the quib runs an impure function.

        Returns `True` is the function of the quib is impure,
        either random function or file reading.

        See Also
        --------
        is_random_func, is_file_loading_func
        Project.reset_impure_quibs

        Returns
        -------
        bool
            Indicating True for impure functions.

        Examples
        --------
        >>> n = iquib(5)
        >>> r = np.random.randint(0, n)
        >>> r.is_impure_func
        True
        """
        return self.is_random_func or self.is_file_loading_func

    @property
    def is_random_func(self) -> bool:
        """
        Indicates whether the quib represents a random function.

        A quib that represents a random function automatically caches its value.
        Thereby, repeated calls to the quib return the same random cached results (quenched randomization).
        This behaviour guarentees mathematical consistency (for example, if ``r`` is a random quib ``s = r - r``
        will always have a value of 0).

        The quib can be re-evaluated (randomized), by invalidating its value either locally using `invalidate()`
        or centrally, using `Project.reset_random_quibs()`

        See Also
        --------
        is_impure_func, is_file_loading_func
        invalidate
        Project.reset_random_quibs

        Returns
        -------
        bool
            Indicating True for random functions.

        Examples
        --------
        >>> n = iquib(5)
        >>> r = np.random.randint(0, n)
        >>> r.is_random_func
        True
        """
        return self.func_definition.is_random_func

    @property
    def is_file_loading_func(self) -> bool:
        """
        Indicates whether the quib represents a function that loads external files.

        A quib whose value depends on the content of external files automatically caches its value.
        Thereby, repeated calls to the quib return the same results even if the file changes.

        The quib can be re-evaluated, by invalidating its value either locally using `invalidate()`
        or centrally, using `Project.reset_file_loading_quibs()`

        See Also
        --------
        is_impure_func, is_random_func
        invalidate
        Project.reset_file_loading_quibs

        Returns
        -------
        bool
            Indicating True for random functions.

        Examples
        --------
        >>> file_name = iquib('my_file.txt')
        >>> x = np.loadtxt(file_name)
        >>> x.is_file_loading_func
        True
        """
        return self.func_definition.is_file_loading_func

    """
    cache
    """

    @property
    def cache_status(self) -> CacheStatus:
        """
        The status of the quib's cache.

        Returns
        -------
        CacheStatus :
            ALL_INVALID: the cache is fully invalid, or the quib is not caching.
            ALL_VALID: The cache is fully valid.
            PARTIAL: Only part of the quib's cache is valid.

        See Also:
        cache_behavior
        """
        return self.handler.quib_function_call.cache.get_cache_status() \
            if self.handler.quib_function_call.cache is not None else CacheStatus.ALL_INVALID

    @property
    def cache_behavior(self):
        """
        Set the value caching mode for the quib:
        'auto':     caching is decided automatically according to the ratio between evaluation time and
                    memory consumption.
        'off':      do not cache.
        'on':       always caching.

        Returns
        -------
        'auto', 'on', or 'off'

        See Also
        --------
        CacheBehavior
        cache_status
        """
        return self.handler.quib_function_call.get_cache_behavior().value

    @cache_behavior.setter
    @validate_user_input(cache_behavior=(str, CacheBehavior))
    def cache_behavior(self, cache_behavior: Union[str, CacheBehavior]):
        cache_behavior = get_enum_by_str(CacheBehavior, cache_behavior)
        if self.is_random_func and cache_behavior != CacheBehavior.ON:
            raise InvalidCacheBehaviorForQuibException(self.handler.quib_function_call.default_cache_behavior) from None
        self.handler.quib_function_call.default_cache_behavior = cache_behavior

    def invalidate(self):
        """
        Invalidate the quib value.

        Invalidate the value of the quib and the value of any downstream dependent quibs, and re-evaluate any
        graphical quibs.

        Returns
        -------
        None
        """
        self.handler.invalidate_self([])
        self.handler.invalidate_and_redraw_at_path([])

    """
    Graphics
    """

    @property
    def is_graphics_func(self):
        """
        Specifies whether the function runs by the quib is a graphics function.

        `True` for known graphics functions
        `False` for known non-graphics functions
        `None` for functions that may create graphics (such as for user functions).

        Returns
        -------
        True, False, or None

        See Also
        --------
        is_graphics_quib, graphics_update_type
        """
        return self.func_definition.is_graphics_func

    @property
    def is_graphics_quib(self):
        """
        Specifies whether the quib is a graphics quib.

        A quib is defined as graphics if its function is a known graphics function (`is_graphics_func`=`True`),
        or if its function created graphics.

        A quib defined as graphics will get auto-refreshed based on the `graphics_update_type`.

        Returns
        -------
        bool

        See Also
        --------
        is_graphics_func, graphics_update_type
        Project.refresh_graphics
        """
        return self.func_definition.is_graphics_func or self.handler.quib_function_call.created_graphics

    @property
    def graphics_update_type(self) -> Union[None, str]:
        """
        Return the graphics_update_type indicating whether the quib should refresh upon upstream assignments.
        Options are:
        "drag":     refresh immediately as upstream objects are dragged
        "drop":     refresh at end of dragging upon graphic object drop.
        "central":  do not automatically refresh. Refresh, centrally upon refresh_graphics().
        "never":    Never refresh.

        Returns
        -------
        "drag", "drop", "central", "never", or None

        See Also
        --------
        UpdateType, Project.refresh_graphics
        """
        return self.handler.graphics_update_type.value if self.handler.graphics_update_type else None

    @graphics_update_type.setter
    @validate_user_input(graphics_update_type=(type(None), str, UpdateType))
    def graphics_update_type(self, graphics_update_type: Union[None, str, UpdateType]):
        self.handler.graphics_update_type = get_enum_by_str(UpdateType, graphics_update_type, allow_none=True)

    """
    Assignment
    """

    @property
    def allow_overriding(self):
        """
        Indicates whether the quib can be overridden.
        The default for allow_overriding is True for iquibs and False in function quibs.

        Returns
        -------
        bool

        See Also
        --------
        assign, assigned_quibs
        """
        return self.handler.allow_overriding

    @allow_overriding.setter
    @validate_user_input(allow_overriding=bool)
    def allow_overriding(self, allow_overriding: bool):
        self.handler.allow_overriding = allow_overriding

    @raise_quib_call_exceptions_as_own
    def assign(self, value: Any, key: Optional[Any] = NoValue) -> None:
        """
        Assign a specified value to the whole array, or to a specific key if specified
        """
        from pyquibbler import default

        key = copy_and_replace_quibs_with_vals(key)
        value = copy_and_replace_quibs_with_vals(value)
        path = [] if key is NoValue else [PathComponent(component=key, indexed_cls=self.get_type())]
        if value is default:
            self.handler.remove_override(path)
        else:
            self.handler.apply_assignment(Assignment(path=path, value=value))

    def __setitem__(self, key, value):
        from pyquibbler import default

        key = copy_and_replace_quibs_with_vals(key)
        value = copy_and_replace_quibs_with_vals(value)
        path = [PathComponent(component=key, indexed_cls=self.get_type())]
        if value is default:
            self.handler.remove_override(path)
        else:
            self.handler.apply_assignment(Assignment(value=value, path=path))

    @property
    def assigned_quibs(self) -> Union[None, Set[Quib, ...]]:
        """
        Set of quibs to which assignments to this quib could translate to and override.

        When assigned_quibs is None, a dialog will be used to choose between options.

        Returns
        -------
        None or set of Quib

        See Also
        --------
        assign, allow_overriding
        """
        return self.handler.assigned_quibs

    @assigned_quibs.setter
    def assigned_quibs(self, quibs: Optional[Iterable[Quib]]) -> None:
        if quibs is not None:
            try:
                quibs = set(quibs)
                if not all(map(lambda x: isinstance(x, Quib), quibs)):
                    raise Exception
            except Exception:
                raise InvalidArgumentValueException(
                    var_name='assigned_quibs',
                    message='a set of quibs.',
                ) from None

        self.handler.assigned_quibs = quibs

    @property
    def assignment_template(self) -> AssignmentTemplate:
        """
        Returns an AssignmentTemplate object indicating type and range restricting assignments to the quib.

        See Also
        --------
        assign
        AssignmentTemplate
        """
        return self.handler.assignment_template

    @assignment_template.setter
    @validate_user_input(template=AssignmentTemplate)
    def assignment_template(self, template):
        self.handler.assignment_template = template

    def set_assignment_template(self, *args) -> None:
        """
        Sets an assignment template for the quib.

        The assignment template restricts the values of any future assignments to the quib.

        Options:
        Set a specific AssignmentTemplate object:

        >>> quib.set_assignment_template(assignment_template)

        Set a bound template between `start` and `stop`:

        >>> quib.set_assignment_template(start, stop)

        Set a bound template between `start` and `stop`, with specified `step`

        >>> quib.set_assignment_template(start, stop, step)

        Remove the assignment_template:

        >>> quib.set_assignment_template(None)

        See Also
        --------
        AssignmentTemplate, assignment_template
        """
        self.handler.assignment_template = create_assignment_template(*args)

    """
    setp
    """

    def setp(self,
             allow_overriding: bool = NoValue,
             assignment_template: Union[tuple, AssignmentTemplate] = NoValue,
             save_directory: Union[str, pathlib.Path] = NoValue,
             save_format: Union[None, str, SaveFormat] = NoValue,
             cache_behavior: Union[str, CacheBehavior] = NoValue,
             assigned_name: Union[None, str] = NoValue,
             name: Union[None, str] = NoValue,
             graphics_update_type: Union[None, str] = NoValue,
             assigned_quibs: set["Quib"] = NoValue,
             ):
        """
        Set one or more properties on a quib.

        Settable properties:
         allow_overriding: bool
         assignment_template: Union[tuple, AssignmentTemplate],
         save_directory: Union[str, pathlib.Path],
         save_format: Union[None, str, SaveFormat],
         cache_behavior: Union[str, CacheBehavior],
         assigned_name: Union[None, str],
         name: Union[None, str],
         graphics_update_type: Union[None, str]

        Examples:
            >>>> a = iquib(7).setp(assigned_name='my_number')
            >>>> b = (2 * a).setp(allow_overriding=True)
        """

        from pyquibbler.quib.factory import get_quib_name
        if allow_overriding is not NoValue:
            self.allow_overriding = allow_overriding
        if assignment_template is not NoValue:
            self.set_assignment_template(assignment_template)
        if save_directory is not NoValue:
            self.save_directory = save_directory
        if save_format is not NoValue:
            self.save_format = save_format
        if cache_behavior is not NoValue:
            self.cache_behavior = cache_behavior
        if assigned_name is not NoValue:
            self.assigned_name = assigned_name
        if name is not NoValue:
            self.assigned_name = name
        if graphics_update_type is not NoValue:
            self.graphics_update_type = graphics_update_type
        if assigned_quibs is not NoValue:
            self.assigned_quibs = assigned_quibs

        var_name = get_quib_name()
        if var_name:
            self.assigned_name = var_name

        return self

    """
    iterations
    """

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

    """
    get_value
    """

    @raise_quib_call_exceptions_as_own
    def get_value_valid_at_path(self, path: Optional[Path]) -> Any:
        """
        Get the actual data that this quib represents, valid at the path given in the argument.
        The value will necessarily return in the shape of the actual result, but only the values at the given path
        are guaranteed to be valid.

        Returns
        -------
        any

        See Also
        --------
        get_value
        """
        return self.handler.get_value_valid_at_path(path)

    @raise_quib_call_exceptions_as_own
    def get_value(self) -> Any:
        """
        Returns the entire value of the quib.

        Runs the function of the quib and returns the result.

        Returns
        -------
        any
            the result of the function of the quib.

        See Also
        --------
        get_shape, get_ndim, get_type
        """
        return self.handler.get_value_valid_at_path([])

    @raise_quib_call_exceptions_as_own
    def get_type(self) -> Type:
        """
        Returns the shape of the quib's value.

        Implements `type` of the value of the quib.

        Returns
        -------
        type
            the type of the quib's value.

        See Also
        --------
        get_value, get_ndim, get_shape

        Note
        ----
        Calculating the type does not necessarily require calculating its entire value.
        """
        return self.handler.quib_function_call.get_type()

    @raise_quib_call_exceptions_as_own
    def get_shape(self) -> Tuple[int, ...]:
        """
        Returns the shape of the quib's value.

        Implements `np.shape` of the value of the quib.

        Returns
        -------
        tuple of int
            the shape of the quib's value.

        See Also
        --------
        get_value, get_ndim, get_type

        Note
        ----
        Calculating the shape does not necessarily require calculating its entire value.
        """
        return self.handler.quib_function_call.get_shape()

    @raise_quib_call_exceptions_as_own
    def get_ndim(self) -> int:
        """
        Returns the number of dimensions of the quib's value.

        Implements `np.ndim` of the value of the quib.

        Returns
        -------
        int
            the number of dimensions of the quib's value.

        See Also
        --------
        get_value, get_shape, get_type

        Note
        ----
        Calculating ndim does not necessarily require calculating its entire value.
        """
        return self.handler.quib_function_call.get_ndim()

    """
    overrides
    """

    def get_override_list(self) -> Overrider:
        """
        Returns an Overrider object representing a list of overrides performed on the quib.

        Returns
        -------
        Overrider
            an object holding a list of all the assignments to the quib.

        See Also
        --------
        assign, assigned_quibs
        """
        return self.handler.overrider

    def get_override_mask(self):
        """
        Returns a quib whos value is the override mask of the current quib.

        Assuming this quib represents a numpy ndarray, return a quib representing its override mask.

        The override mask is a boolean array of the same shape, in which every value is
        set to True if the matching value in the array is overridden, and False otherwise.

        See Also
        --------
        get_override_list
        """
        from pyquibbler.quib.specialized_functions import proxy
        quib = self.args[0] if self.func == proxy else self
        if issubclass(quib.get_type(), np.ndarray):
            mask = np.zeros(quib.get_shape(), dtype=np.bool)
        else:
            mask = recursively_run_func_on_object(func=lambda x: False, obj=quib.get_value())
        return quib.handler.overrider.fill_override_mask(mask)

    """
    relationships
    """

    @property
    def children(self) -> Set[Quib]:
        """
        Returns the set of quibs that are immediate dependants of the current quib.

        Returns
        -------
        set of Quib

        See Also
        --------
        ancestors, parents
        """
        return set(self.handler.children)

    def get_descendants(self) -> Set[Quib]:
        children = self.children
        for child in self.children:
            children |= child.get_descendants()
        return children

    @property
    def parents(self) -> Set[Quib]:
        """
        Returns the set of quibs that this quib depends on.

        Returns
        -------
        set of Quib

        See Also
        --------
        ancestors, children
        """
        return set(self.handler.quib_function_call.get_objects_of_type_in_args_kwargs(Quib))

    @cached_property
    def ancestors(self) -> Set[Quib]:
        """
        Returns all ancestors of the quib, going recursively up the tree.

        Returns
        -------
        set of Quib

        See Also
        --------
        parents, children
        """
        ancestors = set()
        for parent in self.parents:
            ancestors.add(parent)
            ancestors |= parent.ancestors
        return ancestors

    """
    File saving
    """

    @property
    def project(self) -> Project:
        """
        The project object that the quib belongs to.

        The Project provides global functionality inclduing save, load, sync of all quibs,
        undo, redo, and randomization of random quibs.

        Returns
        -------
        Project

        See Also
        --------
        Project
        """
        return self.handler.project

    @property
    def save_format(self):
        """
        Indicates the file format in which quib assignments are saved.

        Options:
            'txt' - save assignments as text file.
            'binary' - save assignments as a binary file.
            'value_txt' - save the quib value as a text file.
            `None` - yield to the Project default save_format

        See Also
        --------
         SaveFormat
        """
        return self.handler.save_format

    @save_format.setter
    @validate_user_input(save_format=(type(None), str, SaveFormat))
    def save_format(self, save_format):
        save_format = get_enum_by_str(SaveFormat, save_format, allow_none=True)
        if (save_format in [SaveFormat.VALUE_BIN, SaveFormat.VALUE_TXT]) and not self.is_iquib:
            raise CannotSaveFunctionQuibsAsValueException

        self.handler.save_format = save_format
        self.handler.on_file_name_change()

    @property
    def actual_save_format(self) -> SaveFormat:
        """
        The actual save_format used by the quib.

        The quib's actual_save_format is its save_format if defined.
        Otherwise it defaults to the project's save_format.

        Returns
        -------
        SaveFormat

        See Also
        --------
        save_format
        SaveFormat
        """
        actual_save_format = self.save_format if self.save_format else self.project.save_format
        if not self.is_iquib:
            actual_save_format = SAVE_FORMAT_TO_FQUIB_SAVE_FORMAT[actual_save_format]
        return actual_save_format

    @property
    def file_path(self) -> Optional[PathWithHyperLink]:
        """
        The full path for the file where quib assignments are saved.
        The path is defined as the [actual_save_directory]/[assigned_name].ext
        ext is determined by the actual_save_format

        Returns
        -------
        pathlib.Path or None

        See Also
        --------
        save_directory, actual_save_directory
        save_format, actual_save_format
        assigned_name
        Project.directory
        """
        return self._get_file_path()

    def _get_file_path(self, response_to_file_not_defined: ResponseToFileNotDefined = ResponseToFileNotDefined.IGNORE) \
            -> Optional[PathWithHyperLink]:

        if self.assigned_name is None or self.actual_save_directory is None or self.actual_save_format is None:
            path = None
            exception = FileNotDefinedException(
                self.assigned_name, self.actual_save_directory, self.actual_save_format)
            if response_to_file_not_defined == ResponseToFileNotDefined.RAISE:
                raise exception
            elif response_to_file_not_defined == ResponseToFileNotDefined.WARN \
                    or response_to_file_not_defined == ResponseToFileNotDefined.WARN_IF_DATA \
                    and self.handler.is_overridden:
                warnings.warn(str(exception))
        else:
            path = PathWithHyperLink(self.actual_save_directory /
                                     (self.assigned_name + SAVE_FORMAT_TO_FILE_EXT[self.actual_save_format]))

        return path

    @property
    def save_directory(self) -> PathWithHyperLink:
        """
        The directory where quib assignments are saved.

        Can be set to a str or Path object.

        If the directory is absolute, it is used as is.
        If directory is relative, it is used relative to the project directory.
        If directory is None, the project directory is used.

        Returns
        -------
        pathlib.Path

        See Also
        --------
        file_path
        """
        return PathWithHyperLink(self.handler.save_directory)

    @save_directory.setter
    @validate_user_input(directory=(str, pathlib.Path))
    def save_directory(self, directory: Union[str, pathlib.Path]):
        if isinstance(directory, str):
            directory = pathlib.Path(directory)
        self.handler.save_directory = directory
        self.handler.on_file_name_change()

    @property
    def actual_save_directory(self) -> Optional[pathlib.Path]:
        """
        The actual directory where quib file is saved.

        By default, the quib's save_directory is None and the actual_save_directory defaults to the
        project's save_directory.
        Otherwise, if the quib's save_directory is defined as an absolute directory then it is used as is,
        and if it is defined as a relative path it is used relative to the project's directory.

        Returns
        -------
        pathlib.Path

        See Also
        --------
        save_directory
        Project.directory
        SaveFormat
        """
        save_directory = self.handler.save_directory
        if save_directory is not None and save_directory.is_absolute():
            return save_directory  # absolute directory
        elif self.project.directory is None:
            return None
        else:
            return self.project.directory if save_directory is None \
                else self.project.directory / save_directory

    def save(self, response_to_file_not_defined: ResponseToFileNotDefined = ResponseToFileNotDefined.RAISE):
        """
        Save the quib assignments to file.

        See Also
        --------
        load, sync
        save_directory, actual_save_directory
        save_format, actual_save_format
        assigned_name
        Project.directory
        """
        if self._get_file_path(response_to_file_not_defined) is not None:
            self.handler.file_syncer.save()

    def load(self, response_to_file_not_defined: ResponseToFileNotDefined = ResponseToFileNotDefined.RAISE):
        """
        Load quib assignments from the quib's file.

        See Also
        --------
        save, sync
        save_directory, actual_save_directory
        save_format, actual_save_format
        assigned_name
        Project.directory
        """
        if self._get_file_path(response_to_file_not_defined) is not None:
            self.handler.file_syncer.load()

    def sync(self, response_to_file_not_defined: ResponseToFileNotDefined = ResponseToFileNotDefined.RAISE):
        """
        Sync quib assignments with the quib's file.

        If the file was changed it will be read to the quib.
        If the quib assignments were changed, the file will be updated.
        If both changed, a dialog is presented to resolve conflict.

        See Also
        --------
        save, load,
        save_directory, actual_save_directory
        save_format, actual_save_format
        assigned_name
        Project.directory
        """
        if self._get_file_path(response_to_file_not_defined) is not None:
            self.handler.file_syncer.sync()

    """
    Repr
    """

    @property
    def assigned_name(self) -> Optional[str]:
        """
        Returns the assigned_name of the quib

        The assigned_name can either be a name automatically created based on the variable name to which the quib
        was first assigned, or a manually assigned name set by setp or by assigning to assigned_name,
        or None indicating unnamed quib.

        The name must be a string starting with a letter and continuing with alpha-numeric charaters. Spaces
        are also allowed.

        The assigned_name is also used for setting the file name for saving overrides.

        Returns
        -------
        str, None

        See Also
        --------
        name, setp, Project.save_quibs, Project.load_quibs
        """
        return self.handler.assigned_name

    @assigned_name.setter
    @validate_user_input(assigned_name=(str, type(None)))
    def assigned_name(self, assigned_name: Optional[str]):
        if assigned_name is None \
                or len(assigned_name) \
                and assigned_name[0].isalpha() and all([c.isalnum() or c in ' _' for c in assigned_name]):
            self.handler.assigned_name = assigned_name
            self.handler.on_file_name_change()
        else:
            raise ValueError('name must be None or a string starting with a letter '
                             'and continuing alpha-numeric characters or spaces')

    @property
    def name(self) -> Optional[str]:
        """
        Returns the name of the quib

        The name of the quib can either be the given assigned_name if not None,
        or an automated name representing the function of the quib (the functional_representation attribute).

        Assigning into name is equivalent to assigning into assigned_name

        Returns
        -------
        str

        See Also
        --------
        assigned_name, setp, functional_representation
        """
        return self.assigned_name or self.functional_representation

    @name.setter
    def name(self, name: str):
        self.assigned_name = name

    def _get_functional_representation_expression(self) -> MathExpression:
        try:
            return pretty_convert.get_pretty_value_of_func_with_args_and_kwargs(self.func, self.args, self.kwargs)
        except Exception as e:
            logger.warning(f"Failed to get repr {e}")
            return FailedMathExpression()

    @property
    def functional_representation(self) -> str:
        """
        Returns a string representing a functional representation of the quib.

        Returns
        -------
        str

        See Also
        --------
        name
        assigned_name
        functional_representation
        pretty_repr
        get_math_expression

        Examples
        --------
        >>> a = iquib(4)
        >>> a.functional_representation
        "iquib(4)"
        """
        return str(self._get_functional_representation_expression())

    def get_math_expression(self) -> MathExpression:
        return NameMathExpression(self.assigned_name) if self.assigned_name is not None \
            else self._get_functional_representation_expression()

    def ugly_repr(self):
        """
        Returns a simple representation of the quib.

        Returns
        -------
        str

        See Also
        --------
        name
        assigned_name
        functional_representation
        pretty_repr
        get_math_expression
        """
        return f"<{self.__class__.__name__} - {self.func}"

    def pretty_repr(self) -> str:
        """
        Returns a pretty representation of the quib.

        Return
        ------
        str

        See Also
        --------
        name
        assigned_name
        functional_representation
        ugly_repr
        get_math_expression
        """
        return f"{self.assigned_name} = {self.functional_representation}" \
            if self.assigned_name is not None else self.functional_representation

    def __repr__(self):
        return str(self)

    def __str__(self):
        if PRETTY_REPR:
            if REPR_RETURNS_SHORT_NAME:
                return str(self.get_math_expression())
            elif REPR_WITH_OVERRIDES and self.handler.is_overridden:
                return self.pretty_repr() + '\n' + self.handler.overrider.pretty_repr(self.assigned_name)
            return self.pretty_repr()
        return self.ugly_repr()

    @property
    def created_in(self) -> Optional[FileAndLineNumber]:
        """
        The file and line number where the quib was created.

        Returns a FileAndLineNumber object indicating the place where the quib was created.

        None if creation place is unknown.

        Returns
        -------
        FileAndLineNumber or None
        """
        return self.handler.created_in

    @property
    def is_iquib(self) -> bool:
        """
        Returns True if the quib is an input quib (iquib).

        Returns
        -------
        bool

        See Also
        --------
        func
        SaveFormat
        """
        return getattr(self.func, '__name__', None) == 'iquib'
