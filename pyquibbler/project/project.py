from __future__ import annotations

import contextlib
import dataclasses
import weakref
from _weakref import ReferenceType
from collections import defaultdict
from pathlib import Path
import sys
from typing import Optional, Set, TYPE_CHECKING, List, Callable
from pyquibbler.utilities.input_validation_utils import validate_user_input
from pyquibbler.utilities.file_path import PathWithHyperLink
from pyquibbler.exceptions import PyQuibblerException
from .actions import Action, AssignmentAction
from pyquibbler.quib.graphics import GraphicsUpdateType
from pyquibbler.file_syncing.types import SaveFormat, ResponseToFileNotDefined

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class NothingToUndoException(PyQuibblerException):

    def __str__(self):
        return "There are no actions left to undo"


class NothingToRedoException(PyQuibblerException):

    def __str__(self):
        return "There are no actions left to redo"


@dataclasses.dataclass
class NoProjectDirectoryException(PyQuibblerException):
    action: str

    def __str__(self):
        return f"The project directory is not define.\n" \
               f"To {self.action} quibs, set the project directory (see set_project_directory)."


class Project:
    """
    A "quibbler" project, giving an interface to get globally collected information (such as all quibs created) and
    performing actions aggregatively on many quibs
    """

    DEFAULT_GRAPHICS_UPDATE = GraphicsUpdateType.DRAG
    DEFAULT_SAVE_FORMAT = SaveFormat.VALUE_TXT

    current_project = None

    def __init__(self, directory: Optional[Path], quib_weakrefs: Set[ReferenceType[Quib]]):
        self._directory = directory
        self._quib_weakrefs = quib_weakrefs
        self._pushing_undo_group = None
        self._undo_action_groups: List[List[Action]] = []
        self._redo_action_groups: List[List[Action]] = []
        self._quib_refs_to_paths_to_released_assignments = defaultdict(dict)
        self._save_format: SaveFormat = self.DEFAULT_SAVE_FORMAT
        self._graphics_update: GraphicsUpdateType = self.DEFAULT_GRAPHICS_UPDATE
        self.on_path_change: Optional[Callable] = None

    @classmethod
    def get_or_create(cls, directory: Optional[Path] = None):
        if cls.current_project is None:
            main_module = sys.modules['__main__']
            directory = directory or (Path(main_module.__file__).parent if hasattr(main_module, '__file__') else None)
            cls.current_project = cls(directory=directory, quib_weakrefs=set())
        return cls.current_project

    """
    quibs
    """

    @property
    def quibs(self) -> Set[Quib]:
        """
        Get all quibs in the project

        Returns
        -------
        set of Quib
        """
        refs_to_remove = set()
        for quib_weakref in self._quib_weakrefs:
            if quib_weakref() is None:
                refs_to_remove.add(quib_weakref)
        for ref in refs_to_remove:
            self._quib_weakrefs.remove(ref)

        return {quib_weakref() for quib_weakref in self._quib_weakrefs}

    def register_quib(self, quib: Quib):
        """
        Register a quib to the project
        """
        self._quib_weakrefs.add(weakref.ref(quib))

    @staticmethod
    def _reset_list_of_quibs(quibs):
        # We aggregate to ensure we don't redraw axes more than once
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        with aggregate_redraw_mode():
            for quib in quibs:
                quib.invalidate()

    """
    central quib commands
    """

    def reset_random_quibs(self):
        """
        Reset and redraw all random quibs in the project.

        Invalidates the cache of all random quibs in the project.
        Any downstream graphics will refresh with new randomization.

        See Also
        --------
        reset_file_loading_quibs, reset_random_quibs, reset_impure_quibs, refresh_graphics
        Quib.is_random
        """
        self._reset_list_of_quibs([quib for quib in self.quibs if quib.is_random])

    def reset_file_loading_quibs(self):
        """
        Reset and then invalidate_redraw all file_loading quibs in the project.

        Invalidates the cache of all file-loading quibs in the project.
        Request for the value of these quibs will cause re-loading of their files.
        Any downstream graphics will automatically update.

        See Also
        --------
        reset_random_quibs, reset_impure_quibs, refresh_graphics
        Quib.is_file_loading
        """
        self._reset_list_of_quibs([quib for quib in self.quibs if quib.is_file_loading])

    def reset_impure_quibs(self):
        """
        Reset and then invalidate_redraw all impure quibs in the project.

        Invalidates the cache of all impure quibs, inclduing random or file-loading quibs in the project.
        Request for the value of these quibs will cause re-loading of their files.
        Any downstream graphics will automatically update.

        See Also
        --------
        reset_file_loading_quibs, reset_random_quibs, refresh_graphics
        Quib.is_impure
        """
        self._reset_list_of_quibs([quib for quib in self.quibs if quib.is_impure])

    def refresh_graphics(self):
        """
        Redraw all graphics function quibs which only redraw when set to 'central'

        See Also
        --------
        reset_file_loading_quibs, reset_random_quibs, reset_impure_quibs, Quib.graphics_update
        Quib.is_graphics, GraphicsUpdateType
        """
        for quib in self.quibs:
            if quib.graphics_update == GraphicsUpdateType.CENTRAL:
                quib.get_value()

    """
    graphics
    """

    @property
    def graphics_update(self) -> GraphicsUpdateType:
        """
        The default mode of updating graphics quibs.

        Quibs whose own graphics_update is None yield to the default graphics_update of the Project.

        Returns
        -------
        GraphicsUpdateType

        See Also
        --------
        Quib.graphics_update
        GraphicsUpdateType
        """
        return self._graphics_update

    @graphics_update.setter
    @validate_user_input(graphics_update=GraphicsUpdateType)
    def graphics_update(self, graphics_update: GraphicsUpdateType):
        self._graphics_update = graphics_update

    """
    save/load
    """

    @property
    def directory(self) -> PathWithHyperLink:
        """
        The directory to which quibs are saved.

        Can be set as a str or Path object.
        None indicates undefined path.

        path = None indicates undefined path.

        Returns
        -------
        PathWithHyperLink or None
        """
        return None if self._directory is None else PathWithHyperLink(self._directory)

    @directory.setter
    @validate_user_input(path=(type(None), str, Path))
    def directory(self, path: Optional[Path]):
        if isinstance(path, str):
            path = Path(path)
        self._directory = None if path is None else path.resolve()

        for quib in self.quibs:
            quib.handler.on_project_directory_change()

        if self.on_path_change:
            self.on_path_change(path)

    @property
    def save_format(self) -> SaveFormat:
        """
        The default file format for saving quibs.

        Options:
            'off': do not save

            'txt': save quib assignments as text if possible (.txt)

            'bin': save quib assignments as a binary file (.quib)

            'value_txt':
                for iquibs: save the value, rather than the assignments, as text (if possible).
                for fquibs: save assignments as text (if possible).

            'value_bin':
                for iquibs: save the value, rather than the assignments, as binary.
                for fquibs: save assignments as binary.

        Quibs whose own save_format is None yield to this default save_format of the Project.

        Returns
        -------
        SaveFormat

        See Also
        --------
        Quib.save_format
        SaveFormat
        """
        return self._save_format

    @save_format.setter
    @validate_user_input(save_format=SaveFormat)
    def save_format(self, save_format: SaveFormat):
        self._save_format = save_format

    def save_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        """
        Save quib assignments to files.

        Saves the assignments of all quibs which have overrides, have an assigned_name and their
        actual_save_format is not 'off'.

        See Also
        --------
        load_quibs, sync_quibs,
        Quib.save_format, Quib.actual_save_format, Project.save_format
        """
        if self.directory is None:
            raise NoProjectDirectoryException(action='save')
        for quib in self.quibs:
            quib.save(response_to_file_not_defined)

    def load_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        """
        Load quib assignments from files.

        Loads assignments from files for all quibs which have an assigned_name and their
        save_format is not 'off'.
        """
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        if self.directory is None:
            raise NoProjectDirectoryException(action='load')
        with aggregate_redraw_mode():
            for quib in self.quibs:
                quib.load(response_to_file_not_defined)

    def sync_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        """
        Sync quib assignments with files.

        Syncs quib assignments with files for all quibs which have an assigned_name and their
        actual_save_format is not 'off'.

        See Also
        --------
        save_quibs, load_quibs
        Quib.save_format, Quib.actual_save_format, Project.save_format
        """
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        if self.directory is None:
            raise NoProjectDirectoryException(action='sync')
        with aggregate_redraw_mode():
            for quib in self.quibs:
                quib.sync(response_to_file_not_defined)

    """
    undo/redo
    """""

    @contextlib.contextmanager
    def start_undo_group(self):
        self._pushing_undo_group = []
        yield
        if self._pushing_undo_group:
            self._undo_action_groups.append(self._pushing_undo_group)
        self._pushing_undo_group = None

    def can_undo(self):
        """
        Indicates whether or not an assignment undo exists.

        Returns
        -------
        bool

        See Also:
        --------
        can_redo
        """
        return len(self._undo_action_groups) > 0

    def can_redo(self):
        """
        Indicates whether or not an assignment redo exists.

        Returns
        -------
        bool

        See Also
        --------
        can_undo
        """
        return len(self._redo_action_groups) > 0

    def _set_released_assignment_for_quib(self, quib, assignment):
        if assignment is not None:
            weak_ref = weakref.ref(quib, lambda k: self._quib_refs_to_paths_to_released_assignments.pop(k))
            paths_to_released_assignments = self._quib_refs_to_paths_to_released_assignments[weak_ref]
            from pyquibbler.path import get_hashable_path
            paths_to_released_assignments[get_hashable_path(assignment.path)] = assignment

    def undo(self):
        """
        Undo the last quib assignment.

        See Also
        --------
        redo
        """
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        try:
            actions = self._undo_action_groups.pop(-1)
        except IndexError:
            raise NothingToUndoException() from None
        with aggregate_redraw_mode():
            for action in actions:
                action.undo()
                if isinstance(action, AssignmentAction):
                    self._set_released_assignment_for_quib(action.quib, action.previous_assignment)

        self._redo_action_groups.append(actions)

    def redo(self):
        """
        Redo the last quib assignment.

        See Also
        --------
        undo
        """
        try:
            actions = self._redo_action_groups.pop(-1)
        except IndexError:
            raise NothingToRedoException() from None

        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        with aggregate_redraw_mode():
            for action in actions:
                action.redo()
                if isinstance(action, AssignmentAction):
                    self._set_released_assignment_for_quib(action.quib, action.new_assignment)

        self._undo_action_groups.append(actions)

    def clear_undo_and_redo_stacks(self, *_, **__):
        """
        Clear the undo/redo stack.
        """
        self._undo_action_groups = []
        self._redo_action_groups = []

    def push_assignment_to_undo_stack(self, quib, overrider, assignment, index):
        from pyquibbler.project import AssignmentAction
        from pyquibbler.path import get_hashable_path
        assignment_hashable_path = get_hashable_path(assignment.path)
        previous_assignment = self._quib_refs_to_paths_to_released_assignments.get(weakref.ref(quib), {}).get(
            assignment_hashable_path
        )
        assignment_action = AssignmentAction(
            quib_ref=weakref.ref(quib, self.clear_undo_and_redo_stacks),
            overrider=overrider,
            previous_index=index,
            new_assignment=assignment,
            previous_assignment=previous_assignment
        )
        self._set_released_assignment_for_quib(quib, assignment)
        if self._pushing_undo_group is not None:
            self._pushing_undo_group.insert(0, assignment_action)
        else:
            self._undo_action_groups.append([assignment_action])

        self._redo_action_groups.clear()
