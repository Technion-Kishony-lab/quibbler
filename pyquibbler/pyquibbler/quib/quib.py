from __future__ import annotations

import copy
import pathlib
import weakref
import warnings

import numpy as np
from matplotlib import pyplot

from pyquibbler.assignment.assignment import AssignmentWithTolerance
from pyquibbler.assignment.default_value import missing
from pyquibbler.assignment.simplify_assignment import AssignmentSimplifier
from pyquibbler.function_definitions import get_definition_for_function, FuncArgsKwargs
from pyquibbler.ipywidget_viewer.quib_widget import QuibWidget
from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
from pyquibbler.quib.types import FileAndLineNumber
from pyquibbler.utilities.file_path import PathWithHyperLink
from typing import Set, Any, TYPE_CHECKING, Optional, Tuple, Type, List, Union, Iterable, Mapping, Callable, Iterator
from weakref import WeakSet

from matplotlib.artist import Artist

from pyquibbler.env import LEN_RAISE_EXCEPTION, BOOL_RAISE_EXCEPTION, \
    PRETTY_REPR, REPR_RETURNS_SHORT_NAME, REPR_WITH_OVERRIDES, ITER_RAISE_EXCEPTION, WARN_ON_UNSUPPORTED_BACKEND
from pyquibbler.graphics import SUPPORTED_BACKENDS
from pyquibbler.quib.quib_guard import guard_raise_if_not_allowed_access_to_quib, \
    CannotAccessQuibInScopeException
from pyquibbler.quib.pretty_converters import MathExpression, FailedMathExpression, \
    NameMathExpression, pretty_convert
from pyquibbler.quib.utils.miscellaneous import copy_and_replace_quibs_with_vals
from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation_with_sources_metadata
from pyquibbler.utilities.input_validation_utils import validate_user_input, InvalidArgumentValueException, \
    get_enum_by_str
from pyquibbler.utilities.iterators import recursively_run_func_on_object
from pyquibbler.utilities.unpacker import Unpacker
from pyquibbler.logger import logger
from pyquibbler.project import Project
from pyquibbler.inversion.exceptions import NoInvertersFoundException
from pyquibbler.path import FailedToDeepAssignException, PathComponent, Path, Paths
from pyquibbler.assignment import InvalidTypeException, get_override_group_for_quib_change, \
    AssignmentTemplate, Overrider, Assignment, AssignmentToQuib, create_assignment_template
from pyquibbler.quib.func_calling.cache_mode import CacheMode
from pyquibbler.quib.external_call_failed_exception_handling import raise_quib_call_exceptions_as_own
from pyquibbler.quib.graphics import GraphicsUpdateType
from pyquibbler.translation.translate import forwards_translate, NoTranslatorsFoundException
from pyquibbler.cache import create_cache, CacheStatus
from pyquibbler.file_syncing import SaveFormat, SAVE_FORMAT_TO_FILE_EXT, \
    ResponseToFileNotDefined, FileNotDefinedException, QuibFileSyncer
from pyquibbler.quib.get_value_context_manager import get_value_context, is_within_get_value_context

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_definition import FuncDefinition
    from pyquibbler.assignment.override_choice import ChoiceContext
    from pyquibbler.assignment import OverrideChoice
    from pyquibbler.quib.func_calling import QuibFuncCall
    from pyquibbler.quib.pretty_converters.quib_viewer import QuibViewer

NoneType = type(None)

FIRST_LINE_OF_FORMATTED_TXT_FILE = '# Formatted Quibbler value file (keep this note)'


class QuibHandler:
    """
    Takes care of all the functionality of a quib.

    Allows the Quib class to only have user functions.

    All data is stored on the QuibHandler (the Quib itself is state-less).
    """

    def __init__(self, quib: Quib, quib_function_call: QuibFuncCall,
                 assignment_template: Optional[AssignmentTemplate],
                 allow_overriding: bool,
                 assigned_name: Optional[str],
                 created_in: Optional[FileAndLineNumber],
                 graphics_update: Optional[GraphicsUpdateType],
                 save_directory: PathWithHyperLink,
                 save_format: Optional[SaveFormat],
                 func: Optional[Callable],
                 args: Tuple[Any, ...] = (),
                 kwargs: Mapping[str, Any] = None,
                 func_definition: FuncDefinition = None,
                 cache_mode: CacheMode = None,
                 has_ever_called_get_value: bool = False
                 ):
        kwargs = kwargs or {}

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
        self.created_in: Optional[FileAndLineNumber] = created_in
        self.graphics_update = graphics_update

        self.save_directory = save_directory

        self.save_format = save_format
        self.func_args_kwargs = FuncArgsKwargs(func, args, kwargs)
        self.func_definition = func_definition

        self.cache_mode = cache_mode

        self._has_ever_called_get_value = has_ever_called_get_value
        self._widget: Optional[QuibWidget] = None

    """
    relationships
    """

    @property
    def quib(self):
        return self._quib_weakref()

    @property
    def project(self) -> Project:
        return Project.get_or_create()

    @property
    def parents(self) -> Iterator[Quib]:
        return self.quib_function_call.get_data_sources() | self.quib_function_call.get_parameter_sources()

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

    def connect_to_parents(self):
        """
        Connect the quib to its parents
        """
        for parent in self.parents:
            parent.handler.add_child(self.quib)

    def disconnect_from_parents(self):
        """
        Disconnect the quib from its parents, so that the quib is effectively inactivated
        """
        for parent in self.parents:
            parent.handler.remove_child(self.quib)

    @property
    def is_iquib(self):
        return getattr(self.func_args_kwargs.func, '__name__', None) == 'iquib'

    """
    properties
    """

    @property
    def actual_graphics_update(self):
        return self.graphics_update or self.project.graphics_update

    def reevaluate_graphic_quib(self):
        """
        Redraws the quib
        """
        self.quib.get_value()

    def _iter_artist_lists(self) -> Iterable[List[Artist]]:
        return map(lambda g: g.artists, self.quib_function_call.flat_graphics_collections())

    def _iter_artists(self) -> Iterable[Artist]:
        return (artist for artists in self._iter_artist_lists() for artist in artists)

    def get_figures(self):
        return {artist.figure for artist in self._iter_artists()}

    """
    Invalidation
    """

    def invalidate_self(self, path: Path):
        """
        Invalidate the quib itself.
        """
        from pyquibbler.quib.graphics.redraw import redraw_quib_with_graphics_or_add_in_aggregate_mode

        if self.quib.is_graphics_quib:
            redraw_quib_with_graphics_or_add_in_aggregate_mode(self.quib, self.actual_graphics_update)

        if len(path) == 0:
            self.quib_function_call.on_type_change()

        self.quib_function_call.invalidate_cache_at_path(path)

    def _invalidate_and_redraw_at_path(self, path: Optional[Path] = None) -> None:
        """
        Perform all actions needed after the quib was mutated (whether by function_definitions or inverse assignment).
        If path is not given, the whole quib is invalidated.
        """
        from pyquibbler import timer
        if path is None:
            path = []

        with timer("quib_invalidation", lambda x: logger.info(f"invalidate {x}")):
            self._invalidate_children_at_path(path)

    def invalidate_and_aggregate_redraw_at_path(self, path: Optional[Path] = None) -> None:
        """
        Perform all actions needed after the quib was mutated (whether by function_definitions or inverse assignment).
        If path is not given, the whole quib is invalidated.
        """
        with aggregate_redraw_mode():
            self._invalidate_and_redraw_at_path(path)

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
            shape=self.quib_function_call.get_shape(),
            type_=self.quib_function_call.get_type(),
            **self.quib_function_call.get_result_metadata()
        )
        return sources_to_forwarded_paths.get(quibs_to_sources[invalidator_quib], [])

    def _get_paths_for_children_invalidation(self, invalidator_quib: Quib,
                                             path: Path) -> Paths:
        """
        Forward translate a path for invalidation, first attempting to do it WITHOUT using getting the shape and type,
        and if/when failure does grace us, we attempt again with shape and type.
        If we have no translators, we forward the path to invalidate all, as we have no more specific way to do it
        """
        # We always invalidate all if it's a parameter source quib
        if invalidator_quib not in self.quib_function_call.get_data_sources() \
                or path == [] \
                or not self.quib_function_call._result_metadata:
            return [[]]

        try:
            return self._forward_translate_with_retrieving_metadata(invalidator_quib, path)
        except NoTranslatorsFoundException:
            return [[]]

    def reset_quib_func_call(self):
        definition = get_definition_for_function(self.func_args_kwargs.func)
        self.quib_function_call = definition.quib_function_call_cls(
            func_args_kwargs=self.func_args_kwargs,
            func_definition=self.func_definition,
            cache_mode=self.cache_mode,
        )
        from pyquibbler.quib.graphics.persist import PersistQuibOnCreatedArtists, PersistQuibOnSettedArtist
        persist_quib_callback = PersistQuibOnSettedArtist if definition.is_artist_setter \
            else PersistQuibOnCreatedArtists
        self.quib_function_call.artists_creation_callback = persist_quib_callback(weakref.ref(self.quib))

    """
    assignments
    """

    @property
    def has_overrider(self) -> bool:
        return self._overrider is not None

    @property
    def overrider(self) -> Overrider:
        if self._overrider is None:
            self._overrider = Overrider()
        return self._overrider

    @property
    def is_overridden(self) -> bool:
        return self._overrider is not None and len(self._overrider) > 0

    def _add_override(self, assignment: Assignment):
        self.overrider.add_assignment(assignment)

        try:
            self._invalidate_and_redraw_at_path(assignment.path)
        except FailedToDeepAssignException as e:
            raise FailedToDeepAssignException(exception=e.exception, path=e.path) from None
        except InvalidTypeException as e:
            raise InvalidTypeException(e.type_) from None

    def override(self, assignment: Union[Assignment, AssignmentWithTolerance]):
        """
        Overrides a part of the data the quib represents.
        """

        from pyquibbler.quib.graphics.redraw import notify_of_overriding_changes_or_add_in_aggregate_mode

        if not self.is_overridden and assignment.is_default():
            return

        # We are shaping the assignment and making it "pretty" in three steps:
        # step 1: round by tolerance:
        if isinstance(assignment, AssignmentWithTolerance):
            assignment = assignment.get_pretty_assignment()

        # step 2: simplify to make it "pretty":
        AssignmentSimplifier(assignment, self.get_value_valid_at_path(None)).simplify()

        # step 3: template the value according to user defined assignment_template:
        if self.assignment_template is not None and not assignment.is_default():
            assignment.value = self.assignment_template.convert(assignment.value)

        self._add_override(assignment)

        self.project.push_assignment_to_pending_undo_group(quib=self.quib,
                                                           assignment=assignment,
                                                           assignment_index=len(self.overrider) - 1)

        self.file_syncer.on_data_changed()

        notify_of_overriding_changes_or_add_in_aggregate_mode(self.quib)

    def apply_assignment(self, assignment: Assignment) -> None:
        """
        Apply an assignment to the quib locally or as inverse assignment to upstream quibs.
        """
        get_override_group_for_quib_change(AssignmentToQuib(self.quib, assignment)).apply()

    def get_inversions_for_assignment(self, assignment: Assignment) -> List[AssignmentToQuib]:
        """
        Get a list of assignments to parent quibs which could be applied instead of the given assignment
        and produce the same change in the value of this quib.
        """
        from pyquibbler.quib.utils.translation_utils import get_func_call_for_translation_with_sources_metadata
        func_call, data_sources_to_quibs = get_func_call_for_translation_with_sources_metadata(self.quib_function_call)

        try:
            value = self.get_value_valid_at_path([])
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
            from pyquibbler.assignment.default_value import default
            if assignment.value is not default:
                # Our cache only accepts shallow paths, so any validation to a non-shallow path is not necessarily
                # overridden at the first component completely- so we ignore it
                if len(assignment.path) <= 1:
                    cache.set_valid_value_at_path(assignment.path, copy.deepcopy(assignment.value))
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
        if self.func_definition.is_graphics \
                and WARN_ON_UNSUPPORTED_BACKEND \
                and pyplot.get_backend() not in SUPPORTED_BACKENDS:
            WARN_ON_UNSUPPORTED_BACKEND.set(False)  # We don't want to warn more than once
            warnings.warn('PyQuibbler is only optimized for the following Matplotlib backends: \n'
                          f'{SUPPORTED_BACKENDS}. \n'
                          'In Jupyter lab, use: %matplotlib tk. \n'
                          'In PyCharm, use: matplotlib.use("TkAgg").')

        try:
            guard_raise_if_not_allowed_access_to_quib(self.quib)
        except CannotAccessQuibInScopeException:
            raise

        with get_value_context(self.quib.pass_quibs):
            if not self._has_ever_called_get_value and Project.get_or_create().autoload_upon_first_get_value:
                self.quib.load(ResponseToFileNotDefined.IGNORE)

            self._has_ever_called_get_value = True

            if path is None:
                paths = [None]
            else:
                paths = self._get_list_of_not_overridden_paths_at_first_component(path)
            result = self.quib_function_call.run(paths)

        return self._overrider.override(result, self.assignment_template) if self.is_overridden else result

    """
    file syncing
    """

    @property
    def actual_save_format(self):
        return self.save_format if self.save_format else self.project.save_format

    def on_project_directory_change(self):
        if not (self.save_directory is not None and self.save_directory.is_absolute()):
            self.file_syncer.on_file_name_changed()

    def on_file_name_change(self):
        self.file_syncer.on_file_name_changed()

    def save_assignments_or_value(self, file_path: pathlib.Path):
        if self.actual_save_format is SaveFormat.OFF:
            return
        if self.actual_save_format is SaveFormat.BIN:
            self.overrider.save_as_binary(file_path)
        if self.actual_save_format is SaveFormat.TXT:
            self.overrider.save_as_txt(file_path)

    def load_from_assignment_file_or_value_file(self, file_path: pathlib.Path):
        if self.actual_save_format is SaveFormat.OFF:
            return
        if self.actual_save_format is SaveFormat.BIN:
            changed_paths = self.overrider.load_from_binary(file_path)
        elif self.actual_save_format is SaveFormat.TXT:
            changed_paths = self.overrider.load_from_txt(file_path)
        else:
            assert False

        self.project.clear_undo_and_redo_stacks()
        if not is_within_get_value_context():
            for path in changed_paths:
                self.invalidate_and_aggregate_redraw_at_path(path)

    def clear_all_overrides(self):
        changed_paths = self.overrider.clear_assignments()

        self.project.clear_undo_and_redo_stacks()
        for path in changed_paths:
            self.invalidate_and_aggregate_redraw_at_path(path)

    """
    Widget
    """

    def on_name_change(self, assigned_name_changed: bool = True):
        if self._widget:
            self._widget.refresh()

        if assigned_name_changed or self.assigned_name is None:
            for child in self.children:
                child.handler.on_name_change(False)

    def on_overrides_changes(self):
        if self._widget:
            self._widget.refresh()

    def display_widget(self) -> bool:
        try:
            from IPython.display import display
            import ipywidgets
        except ImportError:
            return False

        if self._widget is None:
            widget = QuibWidget(self._quib_weakref)
            widget.build_widget()
            widget.refresh()
            self._widget = widget

        display(self._widget.get_widget())

        return True

class Quib:
    """
    A Quib is an object representing a specific call of a function with it's arguments.
    """

    def __init__(self,
                 quib_function_call: QuibFuncCall = None,
                 assignment_template: Optional[AssignmentTemplate] = None,
                 allow_overriding: bool = False,
                 assigned_name: Optional[str] = None,
                 created_in: Optional[FileAndLineNumber] = None,
                 graphics_update: Optional[GraphicsUpdateType] = None,
                 save_directory: Optional[pathlib.Path] = None,
                 save_format: Optional[SaveFormat] = None,
                 func: Optional[Callable] = None,
                 args: Tuple[Any, ...] = (),
                 kwargs: Mapping[str, Any] = None,
                 func_definition: FuncDefinition = None,
                 cache_mode: CacheMode = None,
                 ):

        self.handler = QuibHandler(self, quib_function_call,
                                   assignment_template,
                                   allow_overriding,
                                   assigned_name,
                                   created_in,
                                   graphics_update,
                                   save_directory,
                                   save_format,
                                   func,
                                   args,
                                   kwargs,
                                   func_definition,
                                   cache_mode,
                                   )

    """
    Func metadata
    """

    @property
    def func(self) -> Callable:
        """
        Callable: The function run by the quib.

        A quib calls its function ``func``, with its arguments ``args`` and its keyworded variables ``kwargs``.

        The quib's value is given by ``value = func(*args, **kwargs)``,
        with any quibs in `args` or `kwargs` replaced by their values (unless ``pass_quibs=True``).

        See Also
        --------
        args, kwargs, pass_quibs, is_pure, is_random, is_graphics

        Examples
        --------
        >>> w = iquib(0.5)
        >>> s = np.sin(w)
        >>> s.func
        np.sin
        """
        return self.handler.quib_function_call.func

    @property
    def args(self) -> Tuple[Any]:
        """
        tuple of any: The arguments to be passed to the function run by the quib.

        A quib calls its function ``func``, with its arguments ``args`` and its keyworded variables ``kwargs``.

        The quib's value is given by ``value = func(*args, **kwargs)``.

        `args` is a tuple of all positional arguments, which could each be any object including quibs.
        Any quibs in `args` are replaced with their values when the function is called (unless ``pass_quibs=True``).

        See Also
        --------
        func, kwargs, pass_quibs

        Examples
        --------
        >>> w = iquib(0.5)
        >>> s = w + 10
        >>> s.args
        (w, 10)
        """
        return self.handler.quib_function_call.args

    @property
    def kwargs(self) -> Mapping[str, Any]:
        """
        dict of str to any: The keyworded arguments for the function run by the quib.

        A quib calls its function ``func``, with its arguments ``args`` and its keyworded variables ``kwargs``.

        The quib's value is given by ``value = func(*args, **kwargs)``.

        `kwargs` is a dictionary of str keywords mapped to any object including non-quib or quib arguments.
        Any quibs in `kwargs` are replaced with their values when the function is called (unless ``pass_quibs=True``).

        See Also
        --------
        func, args, pass_quibs

        Examples
        --------
        >>> a = iquib(10)
        >>> s = np.linspace(start=0, stop=a)
        >>> s.kwargs
        {'start': 0, 'stop': a}
        """
        return self.handler.quib_function_call.kwargs

    @property
    def is_impure(self) -> bool:
        """
        bool: Indicates whether the quib runs an impure function.

        True if the function of the quib is impure, either a random function or a file loading function.

        See Also
        --------
        is_random, is_file_loading
        pyquibbler.reset_impure_quibs

        Examples
        --------
        >>> n = iquib(5)
        >>> r = np.random.randint(0, n)
        >>> r.is_impure
        True
        """
        return self.handler.func_definition.is_impure

    @property
    def is_random(self) -> bool:
        """
        bool: Indicates whether the quib represents a random function.

        A quib that represents a random function automatically caches its value.
        Thereby, repeated calls to the quib return the same random cached results (quenched randomization).
        This behaviour guarentees mathematical consistency (for example, if ``r`` is a random quib ``s = r - r``
        will always give a value of 0).

        The quib can be re-evaluated (randomized), by invalidating its value either locally using `invalidate()`
        or centrally, using `qb.reset_random_quibs()`

        See Also
        --------
        is_impure, is_file_loading
        invalidate
        pyquibbler.reset_random_quibs

        Examples
        --------
        >>> n = iquib(5)
        >>> r = np.random.randint(0, n)
        >>> r.is_random
        True
        """
        return self.handler.func_definition.is_random

    @property
    def is_file_loading(self) -> bool:
        """
        bool: Indicates whether the quib represents a function that loads external files.

        A quib whose value depends on the content of external files automatically caches its value.
        Thereby, repeated calls to the quib return the same results even if the file changes.

        The quib can be re-evaluated, by invalidating its value either locally using `invalidate()`
        or centrally, using `qb.reset_file_loading_quibs()`

        See Also
        --------
        is_impure, is_random
        invalidate
        pyquibbler.reset_file_loading_quibs

        Examples
        --------
        >>> file_name = iquib('my_file.txt')
        >>> x = np.loadtxt(file_name)
        >>> x.is_file_loading
        True
        """
        return self.handler.func_definition.is_file_loading

    @property
    def pass_quibs(self) -> bool:
        """
        bool: Indicates whether the quib passes quib arguments to its function.

        Normally, any parent quibs within the `args` and `kwargs` of the focal quib are replaced with their
        values when the quib calls its function (``pass_quibs=False``).

        Setting ``pass_quibs=True``, such quib arguments are passed directly to the quib's function, as quib objects.
        Such behavior is important if we need to allow inverse assignments from graphics created in the function.

        See Also
        --------
        args, kwargs
        """
        return self.handler.func_definition.pass_quibs

    @pass_quibs.setter
    @validate_user_input(pass_quibs=bool)
    def pass_quibs(self, pass_quibs):
        self.handler.func_definition.pass_quibs = pass_quibs

    """
    cache
    """

    @property
    def cache_status(self) -> CacheStatus:
        """
        CacheStatus: The status of the quib's cache.

        ``ALL_INVALID``: the cache is fully invalid, or the quib is not caching.

        ``ALL_VALID``: The cache is fully valid.

        ``PARTIAL``: Only part of the quib's cache is valid.

        See Also
        --------
        CacheStatus, cache_mode
        """
        return self.handler.quib_function_call.cache.get_cache_status() \
            if self.handler.quib_function_call.cache is not None else CacheStatus.ALL_INVALID

    @property
    def cache_mode(self) -> CacheMode:
        """
        CacheMode: The caching mode for the quib.

        Dictates whether the quib should cache its value upon function evaluation.

        Can be set as `CacheMode` or as `str`:

        ``'auto'``:     Caching is decided automatically according to the ratio between evaluation time and
        memory consumption.

        ``'on'``:       Always cache.

        ``'off'``:      Do not cache, unless the quib's function is random or graphics.

        See Also
        --------
        CacheMode, cache_status

        Notes
        -----
        Quibs with random functions and graphics quibs are always cached even when cache mode is ``'off'``.

        """
        return self.handler.cache_mode

    @cache_mode.setter
    @validate_user_input(cache_mode=(str, CacheMode))
    def cache_mode(self, cache_mode: Union[str, CacheMode]):
        self.handler.cache_mode = get_enum_by_str(CacheMode, cache_mode)
        if self.handler.quib_function_call:
            self.handler.quib_function_call.cache_mode = self.handler.cache_mode

    def invalidate(self):
        """
        Invalidate the quib value.

        Invalidate the value of the quib and the value of any downstream dependent quibs.
        Any downstream graphic quibs will be re-evaluated.

        See Also
        --------
        pyquibbler.reset_file_loading_quibs, pyquibbler.reset_random_quibs, pyquibbler.reset_impure_quibs
        """
        self.handler.invalidate_self([])
        self.handler.invalidate_and_aggregate_redraw_at_path([])

    """
    Graphics
    """

    @property
    def is_graphics(self) -> bool:
        """
        bool or None: Specifies whether the function runs by the quib is a graphics function.

        ``True``    for known graphics functions

        ``False``   for known non-graphics functions

        ``None``    auto-detect, for functions that may create graphics (such as for user functions).

        See Also
        --------
        is_graphics_quib, graphics_update
        """
        return self.handler.func_definition.is_graphics

    @property
    def is_graphics_quib(self) -> bool:
        """
        bool: Specifies whether the quib is a graphics quib.

        A quib is defined as graphics if its function is a known graphics function (``is_graphics=True``),
        or if its function's is graphics-auto-detect (``is_graphics=None``) and a call to the function
        created graphics.

        A quib defined as graphics will get auto-refreshed based on the `graphics_update`.

        See Also
        --------
        is_graphics, graphics_update
        pyquibbler.refresh_graphics
        """
        return self.handler.quib_function_call.func_can_create_graphics \
            and not self.handler.created_in_get_value_context

    @property
    def graphics_update(self) -> GraphicsUpdateType:
        """
        GraphicsUpdateType or None: Specifies when the quib should re-evaluate and refresh graphics.

        Can be set to a `GraphicsUpdateType`, or `str`:

        ``'drag'``: Update continuously as upstream quibs are being dragged,
        or upon programmatic assignments to upstream quibs (default for graphics quibs).

        ``'drop'``: Update only at the end of dragging of upstream quibs (at mouse 'drop'),
        or upon programmatic assignments to upstream quibs.

        ``'central'``:  Do not automatically update graphics upon upstream changes.
        Only update upon explicit request for the quibs `get_value()`, or upon the
        central redraw command: `refresh_graphics()`.

        ``'never'``: Do not automatically update graphics upon upstream changes.
        Only update upon explicit request for the quibs `get_value()` (default for non-graphics quibs).

        ``None``: Yield to the default project's graphics_update

        See Also
        --------
        actual_graphics_update, GraphicsUpdateType, Project.graphics_update, pyquibbler.refresh_graphics()
        """
        return self.handler.graphics_update

    @graphics_update.setter
    @validate_user_input(graphics_update=(NoneType, str, GraphicsUpdateType))
    def graphics_update(self, graphics_update: Union[None, str, GraphicsUpdateType]):
        self.handler.graphics_update = get_enum_by_str(GraphicsUpdateType, graphics_update, allow_none=True)

    @property
    def actual_graphics_update(self):
        """
        The actual graphics update mode of the quib.

        The quib's ``actual_graphics_update`` is its ``graphics_update`` if not ``None``.
        Otherwise it defaults to the project's ``graphics_update``.

        See Also
        --------
        graphics_update, Project.graphics_update
        """
        return self.handler.actual_graphics_update

    """
    Assignment
    """

    @property
    def allow_overriding(self) -> bool:
        """
        bool: Indicates whether the quib can be overridden.

        The default for `allow_overriding` is `True` for iquibs and `False` in function quibs.

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
    def assign(self, value: Any, key: Optional[Any] = missing) -> None:
        """
        Assign a value to the whole quib, or to a specific key.

        This method is used to assign a value to a quib. Assigned values can override the
        default value of the focal quib, or can inverse propagate to override the value of
        an upstream quib (inverse propagation is controlled by `assigned_quibs`, `allow_overriding`).

        Assuming ``w`` is a quib:

        ``w.assign(value)`` overrides the quib's value as a whole.

        ``w.assign(value, key)`` overrides the quib at the specified key. This option is equivalent to
        ``w[key] = valye``.


        Parameters
        ----------
        value: any
            A value to assign as an override to the quib's value.

        key: any
            An optional key into which to assign the `value`.

        See Also
        --------
        Inverse-assignments, get_value,
        assigned_quibs, allow_overriding, get_override_list

        Examples
        --------
        Whole-object assignment

        >>> a = iquib([1, 2, 3])
        >>> a.assign('new value')
        >>> a.get_value()
        'new value'

        Item-specific assignment

        >>> a = iquib([1, 2, 3])
        >>> a.assign('new value', 1)
        >>> a.get_value()
        [1, 'new value', 3]
        """

        key = copy_and_replace_quibs_with_vals(key)
        value = copy_and_replace_quibs_with_vals(value)
        path = [] if key is missing else [PathComponent(component=key, indexed_cls=self.get_type())]
        self.handler.apply_assignment(Assignment(value, path))

    def __setitem__(self, key, value):
        key = copy_and_replace_quibs_with_vals(key)
        value = copy_and_replace_quibs_with_vals(value)
        path = [PathComponent(component=key, indexed_cls=self.get_type())]
        self.handler.apply_assignment(Assignment(value, path))

    @property
    def assigned_quibs(self) -> Union[None, Set[Quib, ...]]:
        """
        None or set of Quib: Set of quibs to which assignments to this quib could inverse-translate.

        When ``assigned_quibs=None``, assignments to the quib are inverse-propagated to any upstream quibs
        whose ``allow_overriding=True``.

        When ``assigned_quibs`` is a set of `Quibs`, assignments to the quib are inverse-propagated
        to any upstream quibs in this set whose ``allow_overriding=True``.

        If multiple choices are available for inverse assignment, a dialog is presented to allow choosing between
        these options.

        Setting ``assigned_quibs=set()`` prevents assignments.

        To allow assignment to self, the focal quib or `'self'` can be used within the set of quibs.
        When self is included the ``allow_overriding`` property is automatically set to ``True``.

        Specifying a single quib, or `'self'`, is interpreted as a set containing this single quib.

        See Also
        --------
        assign, allow_overriding
        """
        return self.handler.assigned_quibs

    @assigned_quibs.setter
    def assigned_quibs(self, quibs: Union[None, Union[Quib, str], Iterable[Quib, str]]) -> None:
        if quibs is not None:
            if isinstance(quibs, (list, tuple)):
                quibs = set(quibs)
            elif isinstance(quibs, (str, Quib)):
                quibs = {quibs}

            if 'self' in quibs:
                quibs.remove('self')
                quibs.add(self)

            if not all(map(lambda x: isinstance(x, Quib), quibs)):
                raise InvalidArgumentValueException(
                    var_name='assigned_quibs',
                    message='a set of quibs.',
                ) from None

            if self in quibs:
                self.allow_overriding = True

        self.handler.assigned_quibs = quibs

    @property
    def assignment_template(self) -> AssignmentTemplate:
        """
        AssignmentTemplate: Dictates type and range restricting assignments to the quib.

        See Also
        --------
        assign
        AssignmentTemplate
        set_assignment_template
        """
        return self.handler.assignment_template

    @assignment_template.setter
    @validate_user_input(template=(NoneType, AssignmentTemplate))
    def assignment_template(self, template):
        self.handler.assignment_template = template

    def set_assignment_template(self, *args) -> Quib:
        """
        Sets an assignment template for the quib.

        The assignment template restricts the values of any future assignments to the quib.

        Options:

        * Set a specific AssignmentTemplate object:
            ``set_assignment_template(assignment_template)``

        * Set a bound template between `start` and `stop`:
            ``set_assignment_template(start, stop)``

        * Set a bound template between `start` and `stop`, with specified `step`:
            ``quib.set_assignment_template(start, stop, step)``

        * Remove the `assignment_template`:
            ``set_assignment_template(None)``

        Returns
        -------
        quib: Quib
            The focal quib.

        See Also
        --------
        AssignmentTemplate, assignment_template

        Examples
        --------
        >>> a = iquib(20)
        >>> a.set_assignment_template(0, 100, 10)  # restrict to 0, 10, ..., 100
        >>> a.assign(37)
        >>> a.get_value()
        40
        >>> a.assign(170)
        >>> a.get_value()
        100
        """

        self.handler.assignment_template = create_assignment_template(*args)
        return self
    """
    setp
    """

    def setp(self,
             allow_overriding: bool = missing,
             assignment_template: Union[None, tuple, AssignmentTemplate] = missing,
             save_directory: Union[None, str, pathlib.Path] = missing,
             save_format: Union[None, str, SaveFormat] = missing,
             cache_mode: Union[str, CacheMode] = missing,
             assigned_name: Union[None, str] = missing,
             name: Union[None, str] = missing,
             graphics_update: Union[None, str] = missing,
             assigned_quibs: Optional[Set[Quib]] = missing,
             ) -> Quib:
        """
        Set one or more properties on a quib.

        Parameters
        ----------
        allow_overriding : bool, optional
            Specifies whether the quib is open for overriding assignments.

        assigned_quibs : None or Set[Quib], optional
            Indicates which upstream quibs to inverse-assign to.

        assignment_template : tuple or AssignmentTemplate, optional
            Constrain the type and value of overriding assignments to the quib.

        save_directory : str or pathlib.Path, optional
            The directory to which quib assignments are saved.

        save_format : None, {'off', 'txt', 'bin'}, or SaveFormat, optional
            The file format for saving quib assignments.

        cache_mode : {'auto', 'on', 'off'} or CacheMode, optional
            Indicates whether the quib caches its calculated value.

        assigned_name : None or str, optional
            The user-assigned name of the quib.

        name : None or str, optional
            The name of the quib.

        graphics_update : None or str, optional
            For graphics quibs, indicates when they should be refreshed.

        Returns
        -------
        quib: Quib
            The focal quib.

        See Also
        --------
        allow_overriding, assigned_quibs, assignment_template, save_directory, save_format
        cache_mode, assigned_name, name, graphics_update


        Examples
            >>> a = iquib(7).setp(assigned_name='my_number')
            >>> b = (2 * a).setp(allow_overriding=True)
        """

        from pyquibbler.quib.factory import get_quib_name
        for attr_name in ['allow_overriding', 'save_directory', 'save_format',
                          'cache_mode', 'assigned_name', 'name', 'graphics_update', 'assigned_quibs']:
            value = eval(attr_name)
            if value is not missing:
                setattr(self, attr_name, value)
        if assignment_template is not missing:
            self.set_assignment_template(assignment_template)

        if name is missing and assigned_name is missing and self.assigned_name is None:
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
                            'To get a function quib, use q(len,Q), or quiby(q)(Q). '
                            'To get the len of the current value of Q, use len(Q.get_value()).')
        else:
            return len(self.get_value_valid_at_path(None))

    def __iter__(self):
        """
        Return an iterator to a detected amount of elements requested from the quib.
        """
        if ITER_RAISE_EXCEPTION:
            raise TypeError('Cannot iterate over quibs, as their size can vary. '
                            'Try Quib.iter_first() to iterate over the n-first items of the quib.')
        return Unpacker(self)

    def iter_first(self, amount: Optional[int] = None):
        """
        Return an iterator to the first `amount` elements of the quib.

        ``a, b = quib.iter_first(2)`` is the same as ``a, b = quib[0], quib[1]``.

        When ``amount=None``, quibbler will try to detect the correct amount automatically, and
        might fail with a RuntimeError.
        For example, ``a, b = iquib([1, 2]).iter_first()`` is the same as ``a, b = iquib([1, 2]).iter_first(2)``.
        And even if the quib is larger than the unpacked amount, the iterator will still yield only the first
        items - ``a, b = iquib([1, 2, 3, 4]).iter_first()`` is the same as ``a, b = iquib([1, 2, 3, 4]).iter_first(2)``.

        Returns
        -------
        Iterator of Quib

        Examples
        --------
        >>> @quiby
        ... def sum_and_prod(x):
        ...     return np.sum(x), np.prod(x)
        ...
        >>> nums = iquib([10, 20, 30])
        >>> sum_nums, prod_nums = sum_and_prod(nums).iter_first()
        >>> sum_nums.get_value()
        60

        >>> prod_nums.get_value()
        6000
        """
        return Unpacker(self, amount)

    """
    get_value
    """

    @raise_quib_call_exceptions_as_own
    def get_value_valid_at_path(self, path: Optional[Path]) -> Any:
        """
        Get the value of the quib, valid at the path given in the argument.

        The value will necessarily return with the shape of the actual result, but only the
        values at the given path are guaranteed to be valid.

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
        Calculate the entire value of the quib.

        Run the function of the quib and return the result, or return the value from the cache if valid.

        Returns
        -------
        any
            The result of the function of the quib.

        See Also
        --------
        get_shape, get_ndim, get_type
        """
        return self.handler.get_value_valid_at_path([])

    @raise_quib_call_exceptions_as_own
    def get_type(self) -> Type:
        """
        Return the type of the quib's value.

        Implement ``type`` of the value of the quib.

        Returns
        -------
        type
            The type of the quib's value.

        See Also
        --------
        get_value, get_ndim, get_shape

        Notes
        -----
        Calculating the type does not necessarily require calculating its entire value.
        """
        return self.handler.quib_function_call.get_type()

    @raise_quib_call_exceptions_as_own
    def get_shape(self) -> Tuple[int, ...]:
        """
        Return the shape of the quib's value.

        Implement ``np.shape`` of the value of the quib.

        Returns
        -------
        tuple of int
            The shape of the quib's value.

        See Also
        --------
        get_value, get_ndim, get_type

        Notes
        -----
        Calculating the shape does not necessarily require calculating its entire value.
        """
        return self.handler.quib_function_call.get_shape()

    @raise_quib_call_exceptions_as_own
    def get_ndim(self) -> int:
        """
        Return the number of dimensions of the quib's value.

        Implement ``np.ndim`` of the value of the quib.

        Returns
        -------
        int
            the number of dimensions of the quib's value.

        See Also
        --------
        get_value, get_shape, get_type

        Notes
        -----
        Calculating ndim does not necessarily require calculating its entire value.
        """
        return self.handler.quib_function_call.get_ndim()

    def __bool__(self):
        if BOOL_RAISE_EXCEPTION:
            raise TypeError('bool(Q), where Q is a quib, is not allowed. '
                            'To get a function quib, use q(bool, Q), or quib(bool)(Q). '
                            'To get bool of the current value of Q, use bool(Q.get_value()).')
        else:
            return bool(self.get_value())

    """
    overrides
    """

    def get_override_list(self) -> Optional[Overrider]:
        """
        Return an Overrider object representing a list of overrides performed on the quib.

        Returns
        -------
        Overrider or None
            an object holding a list of all the assignments to the quib.
            `None` if quib is not overridden

        See Also
        --------
        assign, assigned_quibs, allow_overriding
        """
        return self.handler.overrider if self.handler.has_overrider else None

    def get_override_mask(self):
        """
        Return a quib whose value is the override mask of the current quib.

        Assuming this quib represents a numpy `ndarray`, return a quib representing its override mask.

        The override mask is a boolean array of the same shape, in which every value is
        set to True if the matching value in the array is overridden, and False otherwise.

        See Also
        --------
        get_override_list
        """
        from pyquibbler.quib.specialized_functions import proxy
        quib = self.args[0] if self.func == proxy else self
        if issubclass(quib.get_type(), np.ndarray):
            mask = np.zeros(quib.get_shape(), dtype=bool)
        else:
            mask = recursively_run_func_on_object(func=lambda x: False, obj=quib.get_value())
        return quib.handler.overrider.fill_override_mask(mask)

    """
    relationships
    """

    def get_children(self, bypass_intermediate_quibs: bool = False) -> Set[Quib]:
        """
        Return the set of quibs that are immediately downstream of the current quib.

        Parameters
        ----------
        bypass_intermediate_quibs : bool, default: False
            Indicates whether to bypass intermediate quibs.
            Intermediate quibs are defined as unnamed and non-graphics
            quibs (``assigned_name=None`` and ``is_graphics=False``), typically representing
            intermediate calculations.

        Returns
        -------
        Set of Quib
            The set of child quibs

        See Also
        --------
        get_ancestors, get_parents, get_descendants, dependency_graph

        Examples
        --------
        >>> a = iquib(1)
        >>> b = a + 1
        >>> c = (a + 2) * b
        >>> a.get_children()
        {b = a + 1, a + 2}
        >>> a.get_children(True)
        {b = a + 1, c = (a + 2) * b}
        """

        children = set(self.handler.children)
        if not bypass_intermediate_quibs:
            return children

        named_children = set()
        for child in children:
            if child.assigned_name is None and not child.is_graphics_quib:
                named_children |= child.get_children(bypass_intermediate_quibs)
            else:
                named_children.add(child)
        return named_children

    def get_descendants(self, bypass_intermediate_quibs: bool = False, depth: Optional[int] = None) -> Set[Quib]:
        """
        Search for all quibs downstream of current quib.

        Recursively search downstream to find all the quibs that depend on the current quib.

        Parameters
        ----------
        bypass_intermediate_quibs : bool, default: False
            Indicates whether to bypass intermediate quibs.
            Intermediate quibs are defined as unnamed and non-graphics
            quibs (``assigned_name=None`` and ``is_graphics=False``), typically representing
            intermediate calculations.

        depth : int or None
            Depth of search, `0` returns empty set, `1` returns the children, etc.
            `None` for infinite (default).

        Returns
        -------
        Set of Quib
            The set of descendant quibs

        See Also
        --------
        get_ancestors, get_children, get_parents, dependency_graph

        Examples
        --------
        >>> a = iquib(1)
        >>> b = a + 1
        >>> c = (a + 2) * b
        >>> d = b * (c + 1)
        >>> a.get_descendants()
        {b = a + 1, a + 2, c = (a + 2) * b, c + 1, d = b * (c + 1)}
        >>> a.get_descendants(True)
        {b = a + 1, c = (a + 2) * b, d = b * (c + 1)}
        """
        descendants = set()
        if depth is None or depth > 0:
            for child in self.get_children(bypass_intermediate_quibs):
                descendants.add(child)
                descendants |= child.get_descendants(bypass_intermediate_quibs,
                                                     depth if depth is None else depth - 1)
        return descendants

    def get_parents(self, bypass_intermediate_quibs: bool = False, is_data_source: Optional[bool] = None) -> Set[Quib]:
        """
        Return the set of quibs immediate upstream to the current quib.

        The parents are the immediate quibs that this quib depends on, namely the quibs in the args and kwargs
        of the quib function call.

        Parameters
        ----------
        bypass_intermediate_quibs : bool, default: False
            Indicates whether to bypass intermediate quibs.
            Intermediate quibs are defined as unnamed and non-graphics
            quibs (``assigned_name=None`` and ``is_graphics=False``), typically representing
            intermediate calculations.

        is_data_source : bool or None. default: None
            Include only data sources (`True`), only paramter sources (`False`), or both (`None`, default).

        Returns
        -------
        Set of Quib
            The set of parent quibs

        See Also
        --------
        args, kwargs, get_ancestors, get_children, get_descendants, dependency_graph

        Examples
        --------
        >>> a = iquib(1)
        >>> b = iquib(3)
        >>> c = (a + 2) * b
        >>> c.get_parents()
        {a + 2, b = iquib(3)}
        >>> c.get_parents(True)
        {a = iquib(1), b = iquib(3)}
        """
        data_parents = set(self.handler.quib_function_call.get_data_sources())
        parameter_parents = set(self.handler.quib_function_call.get_parameter_sources())
        if is_data_source is True:
            parents = data_parents
        elif is_data_source is False:
            parents = parameter_parents
        else:
            parents = data_parents | parameter_parents

        if not bypass_intermediate_quibs:
            return parents

        named_parents = set()
        for parent in parents:
            if parent.assigned_name is None and not parent.is_graphics_quib:
                named_parents |= parent.get_parents(bypass_intermediate_quibs)
            else:
                named_parents.add(parent)
        return named_parents

    def get_ancestors(self, bypass_intermediate_quibs: bool = False, depth: Optional[int] = None) -> Set[Quib]:
        """
        Search for all upstream quibs that this quib depends on.

        Recursively scan upstream to find all the quibs that this quib depends on.

        Parameters
        ----------
        bypass_intermediate_quibs : bool, default: False
            Indicates whether to bypass intermediate quibs.
            Intermediate quibs are defined as unnamed and non-graphics
            quibs (``assigned_name=None`` and ``is_graphics=False``), typically representing
            intermediate calculations.

        depth : int or None
            Depth of search, `0` returns empty set, `1` returns the parents, etc.
            `None` for infinite (default).

        Returns
        -------
        Set of Quib
            The set of ancestor quibs

        See Also
        --------
        get_parents, get_children, get_descendants, dependency_graph

        Examples
        --------
        >>> a = iquib(1)
        >>> b = iquib(3)
        >>> c = (a + 2) * b
        >>> c.get_ancestors()
        {a = iquib(1), a + 2, b = iquib(3)}
        >>> c.get_ancestors(True)
        {a = iquib(1), b = iquib(3)}
        """
        ancestors = set()
        if depth is None or depth > 0:
            for parent in self.get_parents(bypass_intermediate_quibs):
                ancestors.add(parent)
                ancestors |= parent.get_ancestors(bypass_intermediate_quibs,
                                                  depth if depth is None else depth - 1)
        return ancestors
    """
    File saving
    """

    @property
    def project(self) -> Project:
        """
        Project: The project object that the quib belongs to.

        The Project provides global functionality inclduing save, load, sync of all quibs,
        undo, redo, and randomization of random quibs.

        See Also
        --------
        Project
        """
        return self.handler.project

    @property
    def save_format(self) -> SaveFormat:
        """
        SaveFormat: The file format in which quib assignments are saved.

        Can be set as `SaveFormat` or as `str`, or `None`:

        ``'txt'`` - save assignments as text file.

        ``'bin'`` - save assignments as a binary file.

        ``None`` - yield to the Project default save_format

        See Also
        --------
        SaveFormat
        """
        return self.handler.save_format

    @save_format.setter
    @validate_user_input(save_format=(NoneType, str, SaveFormat))
    def save_format(self, save_format):
        save_format = get_enum_by_str(SaveFormat, save_format, allow_none=True)

        self.handler.save_format = save_format
        self.handler.on_file_name_change()

    @property
    def actual_save_format(self) -> SaveFormat:
        """
        SaveFormat: The actual save_format used by the quib.

        The quib's ``actual_save_format`` is its save_format if defined.
        Otherwise it defaults to the project's ``save_format``.

        See Also
        --------
        save_format
        SaveFormat
        """
        return self.handler.actual_save_format

    @property
    def file_path(self) -> Optional[PathWithHyperLink]:
        """
        pathlib.Path or None: The full path for the file where quib assignments are saved.

        The path is defined as the [actual_save_directory]/[assigned_name].ext
        ext is determined by the actual_save_format

        See Also
        --------
        save_directory, actual_save_directory
        save_format, actual_save_format
        SaveFormat
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
            path = self.actual_save_directory \
                   / (self.assigned_name + SAVE_FORMAT_TO_FILE_EXT[self.actual_save_format])

        return path

    @property
    def save_directory(self) -> PathWithHyperLink:
        """
        PathWithHyperLink: The directory where quib assignments are saved.

        Can be set to a str or Path object.

        If the directory is absolute, it is used as is.

        If directory is relative, it is used relative to the project directory.

        If directory is `None`, the project directory is used.

        See Also
        --------
        file_path
        Project.directory
        """
        return self.handler.save_directory

    @save_directory.setter
    @validate_user_input(directory=(NoneType, str, pathlib.Path))
    def save_directory(self, directory: Union[None, str, pathlib.Path]):
        if isinstance(directory, str):
            directory = PathWithHyperLink(directory)
        self.handler.save_directory = directory
        self.handler.on_file_name_change()

    @property
    def actual_save_directory(self) -> Optional[pathlib.Path]:
        """
        pathlib.Path or None: The actual directory where quib file is saved.

        By default, the quib's save_directory is ``None`` and the ``actual_save_directory`` defaults to the
        project's ``save_directory``.
        Otherwise, if the quib's ``save_directory`` is defined as an absolute directory then it is used as is,
        and if it is defined as a relative path it is used relative to the project's directory.

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

    def save(self,
             response_to_file_not_defined: ResponseToFileNotDefined = ResponseToFileNotDefined.RAISE,
             skip_user_verification: bool = False,
             ):
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
            self.handler.file_syncer.save(skip_user_verification)
            self.handler.on_overrides_changes()

    def load(self,
             response_to_file_not_defined: ResponseToFileNotDefined = ResponseToFileNotDefined.RAISE,
             skip_user_verification: bool = False,
             ):
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
            self.handler.file_syncer.load(skip_user_verification)
            self.handler.on_overrides_changes()

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
            self.handler.on_overrides_changes()

    """
    Repr
    """

    @property
    def assigned_name(self) -> Optional[str]:
        """
        str or None: The assigned_name of the quib.

        The `assigned_name` can either be a name automatically created based on the variable name to which the quib
        was first assigned, or a manually assigned name set by `setp` or by assigning to `assigned_name`,
        or `None` indicating unnamed quib.

        The name must be a string starting with a letter and continuing with an alpha-numeric character. Spaces
        are also allowed.

        See Also
        --------
        name, setp, pyquibbler.save_quibs, pyquibbler.load_quibs

        Notes
        -----
        The `assigned_name` is also used for setting the file name for saving overrides.

        Examples
        --------
        Automatic naming based on quib's variable name:

        >>> data = iquib([1, 2, 3])
        >>> data.assigned_name
        `data`

        Manual naming:

        >>> data = iquib([1, 2, 3], assigned_name='my data')
        >>> data.assigned_name
        `my data`

        """
        return self.handler.assigned_name

    @assigned_name.setter
    @validate_user_input(assigned_name=(str, NoneType))
    def assigned_name(self, assigned_name: Optional[str]):
        if assigned_name is None \
                or len(assigned_name) \
                and assigned_name[0].isalpha() and all([c.isalnum() or c in ' _' for c in assigned_name]):
            self.handler.assigned_name = assigned_name
            self.handler.on_file_name_change()
            self.handler.on_name_change()
        else:
            raise InvalidArgumentValueException('assigned_name',
                                                'name must be None or a string starting with a letter '
                                                'and continuing alpha-numeric characters or spaces.'
                                                )

    @property
    def name(self) -> Optional[str]:
        """
        str: The name of the quib.

        The name of the quib can either be the given `assigned_name` if not `None`,
        or an automated name representing the function of the quib (the `functional_representation` attribute).

        See Also
        --------
        assigned_name, setp, functional_representation

        Notes
        -----
        Assigning into `name` is equivalent to assigning into `assigned_name`.

        Examples
        --------
        >>> number = iquib(7)
        >>> new_number = number + 3
        >>> new_number.name
        `new_number`

        >>> new_number.assigned_name = None
        >>> new_number.name
        `number + 3`
        """
        return self.assigned_name or self.functional_representation

    @name.setter
    def name(self, name: str):
        self.assigned_name = name

    def _get_functional_representation_expression(self) -> MathExpression:
        args = self.args
        kwargs = self.kwargs
        if self.handler.func_definition.kwargs_to_ignore_in_repr:
            kwargs = {k: v for k, v in kwargs.items()
                      if k not in self.handler.func_definition.kwargs_to_ignore_in_repr}
        try:
            from matplotlib.axes import Axes
            if self.handler.func_definition.is_graphics and len(args) > 0 \
                    and isinstance(args[0], Axes):
                return pretty_convert.get_pretty_value_of_func_with_args_and_kwargs(self.func,
                                                                                    args[1:], kwargs)
            if getattr(self.func, 'wrapped__new__', False) and len(args) > 0:
                cls_name = str(args[0])
                short_cls_name = cls_name.split('.')[-1][:-2]
                return pretty_convert.get_pretty_value_of_func_with_args_and_kwargs(short_cls_name,
                                                                                    args[1:], kwargs)

            return pretty_convert.get_pretty_value_of_func_with_args_and_kwargs(self.func,
                                                                                args, kwargs)
        except Exception as e:
            logger.warning(f"Failed to get repr {e}")
            return FailedMathExpression()

    @property
    def functional_representation(self) -> str:
        """
        str: A string representing the function and arguments of the quib.

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
        >>> b = (a + 10) ** 2
        >>> b.functional_representation
        '(a + 10) ** 2'
        """
        return str(self._get_functional_representation_expression())

    def get_math_expression(self) -> MathExpression:
        """
        Return a MathExpression object providing a string representation of the quib.

        See Also
        --------
        functional_representation
        """
        return NameMathExpression(self.assigned_name) if self.assigned_name is not None \
            else self._get_functional_representation_expression()

    @property
    def ugly_repr(self) -> str:
        """
        str: a simple string representation of the quib.

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
        >>> b = np.sin(a)
        >>> b.ugly_repr
        "<Quib - <ufunc 'sin'>"
        """
        return f"<{self.__class__.__name__} - {self.func}>"

    @property
    def pretty_repr(self) -> str:
        """
        str: a pretty string representation of the quib.

        Returns
        -------
        str

        See Also
        --------
        name
        assigned_name
        functional_representation
        ugly_repr
        get_math_expression

        Examples
        --------
        >>> a = iquib(4)
        >>> b = (a + 10) ** 2
        >>> b.functional_representation
        'b = (a + 10) ** 2'
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
                return self.pretty_repr + '\n' + self.handler.overrider.get_pretty_repr(self.assigned_name)
            return self.pretty_repr
        return self.ugly_repr

    def display(self) -> QuibViewer:
        """
        Returns a QuibViewer which displays the properties of the quib.

        Returns
        -------
        QuibViewer

        See Also
        --------
        QuibViewer
        """

        from .pretty_converters.quib_viewer import QuibViewer
        return QuibViewer(self)

    @property
    def created_in(self) -> Optional[FileAndLineNumber]:
        """
        FileAndLineNumber or None: The file and line number where the quib was created.

        Indicates the place where the quib was created.

        `None` if creation place is unknown.

        See Also
        --------
        name, assigned_name
        """
        return self.handler.created_in

    @property
    def is_iquib(self) -> bool:
        """
        bool: Indicates whether the quib is an input quib (iquib).

        See Also
        --------
        func
        save_format
        """
        return self.handler.is_iquib

    def _on_widget_change(self, v):
        self.assigned_name = v['new']

    def _repr_html_(self) -> Optional[str]:
        if self.allow_overriding or self.handler.is_overridden:
            if self.handler.display_widget():
                return ''

        return None
