from __future__ import annotations

import weakref
from collections import defaultdict
from pathlib import Path
import sys
from typing import Optional, Set, List, Callable, Union, Mapping

from pyquibbler.utilities.input_validation_utils import get_enum_by_str, validate_user_input
from pyquibbler.utilities.file_path import PathWithHyperLink
from pyquibbler.quib.graphics import GraphicsUpdateType, aggregate_redraw_mode
from pyquibbler.file_syncing.types import SaveFormat, ResponseToFileNotDefined

from .actions import Action, AddAssignmentAction, AssignmentAction, RemoveAssignmentAction
from .exceptions import NoProjectDirectoryException, NothingToUndoException, NothingToRedoException

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib
    from pyquibbler.assignment import Assignment


class Project:
    """
    Quibbler project providing save/load and undo/redo functionality.

    Keeps a weakref set of all quibs to manage the quibs centrally.
    """

    DEFAULT_GRAPHICS_UPDATE = GraphicsUpdateType.DRAG
    DEFAULT_SAVE_FORMAT = SaveFormat.TXT

    current_project = None

    def __init__(self, directory: Optional[Path]):
        self._directory = directory
        self._quib_refs: weakref.WeakSet[Quib] = weakref.WeakSet()
        self._pending_undo_group: Optional[List] = None
        self._undo_action_groups: List[List[Action]] = []
        self._redo_action_groups: List[List[Action]] = []
        self._quib_refs_to_paths_to_assignment_actions = defaultdict(dict)
        self._save_format: SaveFormat = self.DEFAULT_SAVE_FORMAT
        self._graphics_update: GraphicsUpdateType = self.DEFAULT_GRAPHICS_UPDATE
        self.on_path_change: Optional[Callable] = None
        self.autoload_upon_first_get_value = False

    @classmethod
    def get_or_create(cls, directory: Optional[Path, str] = None):
        """
        Returns the current project.

        Parameters
        ----------
        directory : Path, str or None, default None
            The project directory, to which quibs are saved.
            If None, the project directory is set based on the directory of __main__.

        See Also
        --------
        pyquibbler.get_project
        """

        if Project.current_project is None:
            main_module = sys.modules['__main__']
            directory = directory or (Path(main_module.__file__).parent if hasattr(main_module, '__file__') else None)
            Project.current_project = cls(directory=directory)
        return Project.current_project

    """
    quibs
    """

    @property
    def quibs(self) -> Set[Quib]:
        """
        Set of Quib: All quibs in the project.

        Maintains the set of all quibs in the project.
        """
        return set(self._quib_refs)

    def register_quib(self, quib: Quib):
        """
        Register a quib to the project.
        """
        self._quib_refs.add(quib)

    @staticmethod
    def _reset_list_of_quibs(quibs):
        # We aggregate to ensure we don't redraw axes more than once
        with aggregate_redraw_mode():
            for quib in quibs:
                quib.invalidate()

    """
    central quib commands
    """

    def reset_random_quibs(self):
        """
        Reset the value of all random quibs in the project.

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
        Reset the value of all file-loading quibs in the project.

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
        Reset the value of all impure quibs in the project.

        Invalidates the cache of all impure quibs, including random or file-loading quibs, in the project.
        Request for the value of these quibs will cause re-evaluation of their function.
        Any downstream graphics will automatically update.

        See Also
        --------
        reset_file_loading_quibs, reset_random_quibs, refresh_graphics
        Quib.is_impure
        """
        self._reset_list_of_quibs([quib for quib in self.quibs if quib.is_impure])

    def refresh_graphics(self):
        """
        Redraw all graphics quibs whose graphics_update='central'.

        See Also
        --------
        reset_file_loading_quibs, reset_random_quibs, reset_impure_quibs,
        Quib.graphics_update, Quib.is_graphics, GraphicsUpdateType
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
        GraphicsUpdateType: The default mode of updating graphics for all quibs.

        Quibs whose own graphics_update is ``None`` adhere to the default graphics_update of the Project.

        Can be set to `GraphicsUpdateType` or `str`:

        ``'drag'``: Update continuously as upstream quibs are being dragged,
        or upon programmatic assignments to upstream quibs (default for graphics quibs).

        ``'drop'``: Update only at the end of dragging of upstream quibs (at mouse 'drop'),
        or upon programmatic assignments to upstream quibs.

        ``'central'``:  Do not automatically update graphics upon upstream changes.
        Only update upon explicit request for the quibs `get_value()`, or upon the
        central redraw command: `refresh_graphics()`.

        ``'never'``: Do not automatically update graphics upon upstream changes.
        Only update upon explicit request for the quibs `get_value()` (default for non-graphics quibs).

        See Also
        --------
        Quib.graphics_update
        GraphicsUpdateType
        pyquibbler.refresh_graphics()
        """
        return self._graphics_update

    @graphics_update.setter
    @validate_user_input(graphics_update=(str, GraphicsUpdateType))
    def graphics_update(self, graphics_update: Union[str, GraphicsUpdateType]):
        self._graphics_update = get_enum_by_str(GraphicsUpdateType, graphics_update)

    """
    save/load
    """

    @property
    def directory(self) -> Optional[PathWithHyperLink]:
        """
        PathWithHyperLink or None: The directory to which quib assignments are saved by default.

        Can be set as a `str`, `Path`.

        Quibs whose own save_directory is None adhere to the `directory` of the project.

        Quibs with a relative path as their save_directory, save to
        `Project.directory / Quib.save_directory`

        See Also
        --------
        Quib.save_directory
        """
        return self._directory

    @directory.setter
    @validate_user_input(path=(type(None), str, Path))
    def directory(self, path: Optional[Union[Path, str]]):
        if isinstance(path, str):
            path = PathWithHyperLink(path)
        self._directory = None if path is None else path.resolve()

        for quib in self.quibs:
            quib.handler.on_project_directory_change()

        if self.on_path_change:
            self.on_path_change(path)

    def _raise_if_directory_is_not_defined(self, action: str):
        if self.directory is None:
            raise NoProjectDirectoryException(action=action)

    @property
    def save_format(self) -> SaveFormat:
        """
        SaveFormat: The default file format for saving quibs.

        Quibs whose own `save_format` is `None` yield to this default `save_format` of the Project.

        Can be set as `SaveFormat` or as `str`:

        ``'off'``: do not save

        ``'txt'``: save quib assignments as text if possible (.txt)

        ``'bin'``: save quib assignments as a binary file (.quib)

        See Also
        --------
        Quib.save_format
        Quib.actual_save_format
        SaveFormat
        """
        return self._save_format

    @save_format.setter
    @validate_user_input(save_format=(str, SaveFormat))
    def save_format(self, save_format: Union[str, SaveFormat]):
        self._save_format = get_enum_by_str(SaveFormat, save_format)

    def save_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        """
        Save quib assignments to files.

        Saves the assignments of all quibs which have overrides, have an assigned_name and their
        `actual_save_format` is not 'off'.

        See Also
        --------
        load_quibs, sync_quibs,
        Quib.save_format, Quib.actual_save_format, Project.save_format
        Quib.save
        """
        self._raise_if_directory_is_not_defined('save')
        for quib in self.quibs:
            quib.save(response_to_file_not_defined)

    def load_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        """
        Load quib assignments from files.

        Loads assignments from files for all quibs which have an assigned_name and their
        `actual_save_format` is not 'off'.

        See Also
        --------
        Sync_quibs, load_quibs
        Quib.save_format, Quib.actual_save_format, Project.save_format
        Quib.load
        """
        self._raise_if_directory_is_not_defined('load')
        with aggregate_redraw_mode():
            for quib in self.quibs:
                quib.load(response_to_file_not_defined)

    def sync_quibs(self, response_to_file_not_defined=ResponseToFileNotDefined.WARN_IF_DATA):
        """
        Sync quib assignments with files.

        Syncs quib assignments with files for all quibs which have an assigned_name and their
        `actual_save_format` is not 'off'.

        See Also
        --------
        save_quibs, load_quibs
        Quib.save_format, Quib.actual_save_format, Project.save_format
        Quib.sync
        """
        self._raise_if_directory_is_not_defined('sync')
        with aggregate_redraw_mode():
            for quib in self.quibs:
                quib.sync(response_to_file_not_defined)

    """
    undo/redo
    """""

    def can_undo(self) -> bool:
        """
        Indicates whether an assignment undo exists.

        Returns
        -------
        bool

        See Also
        --------
        can_redo, undo, redo

        Examples
        --------
        >>> a = iquib([1, 2, 3])
        >>> qb.can_undo()
        False
        >>> a[1] = 10
        >>> qb.can_redo()
        True
        >>> qb.undo()
        >>> qb.can_undo()
        False
        """
        return len(self._undo_action_groups) > 0

    def can_redo(self) -> bool:
        """
        Indicates whether an assignment redo exists.

        Returns
        -------
        bool

        See Also
        --------
        can_undo, undo, redo

        Examples
        --------
        >>> a = iquib([1, 2, 3])
        >>> a[1] = 10
        >>> qb.undo()
        >>> qb.can_redo()
        True
        >>> qb.redo()
        >>> qb.can_redo()
        False
        """
        return len(self._redo_action_groups) > 0

    def undo(self):
        """
        Undo the last quib assignment.

        See Also
        --------
        redo, can_undo

        Examples
        --------
        >>> a = iquib([1, 2, 3])
        >>> a[1] = 10
        >>> a.get_value()
        [1, 10, 3]
        >>> qb.undo()
        >>> a.get_value()
        [1, 2, 3]
        """
        try:
            actions = self._undo_action_groups.pop(-1)
        except IndexError:
            raise NothingToUndoException() from None
        with aggregate_redraw_mode():
            for action in actions:
                action.undo()
                if isinstance(action, AssignmentAction):
                    action.quib.handler.on_overrides_changes()

                if isinstance(action, AddAssignmentAction):
                    self._set_previous_assignment_action_for_quib_at_relevant_path(action.quib,
                                                                                   action.assignment.path,
                                                                                   action.previous_assignment_action)

        self._redo_action_groups.append(actions)
        self.set_undo_redo_buttons_enable_state()

    def redo(self):
        """
        Redo the last quib assignment.

        See Also
        --------
        undo, can_redo

        Examples
        --------
        >>> a = iquib([1, 2, 3])
        >>> a[1] = 10
        >>> a.get_value()
        [1, 10, 3]
        >>> qb.undo()
        >>> a.get_value()
        [1, 2, 3]
        >>> qb.redo()
        >>> a.get_value()
        [1, 10, 3]
        """
        try:
            actions = self._redo_action_groups.pop(-1)
        except IndexError:
            raise NothingToRedoException() from None

        with aggregate_redraw_mode():
            for action in actions:
                action.redo()
                if isinstance(action, AssignmentAction):
                    action.quib.handler.on_overrides_changes()

                if isinstance(action, AddAssignmentAction):
                    self._set_previous_assignment_action_for_quib_at_relevant_path(action.quib,
                                                                                   action.assignment.path,
                                                                                   action)

        self._undo_action_groups.append(actions)
        self.set_undo_redo_buttons_enable_state()

    def clear_undo_and_redo_stacks(self, *_, **__):
        """clear_undo_and_redo_stacks()

        Clear the undo/redo stack.

        See Also
        --------
        undo, redo, can_undo, can_redo
        """
        self._undo_action_groups = []
        self._redo_action_groups = []
        self.set_undo_redo_buttons_enable_state()

    def start_pending_undo_group(self):
        self._pending_undo_group = []

    def push_assignment_to_pending_undo_group(self, quib: Quib, assignment: Assignment, assignment_index: int):
        self._pending_undo_group.append((weakref.ref(quib), assignment, assignment_index))

    def push_single_assignment_to_undo_stack(self, quib: Quib, assignment: Assignment, assignment_index: int):
        self.start_pending_undo_group()
        self.push_assignment_to_pending_undo_group(quib, assignment, assignment_index)
        self.push_pending_undo_group_to_undo_stack()

    def push_pending_undo_group_to_undo_stack(self):
        if self._pending_undo_group:
            pushing_undo_group = []
            for quib_ref, assignment, assignment_index in self._pending_undo_group:
                quib = quib_ref()
                if quib is not None:
                    pushing_undo_group.insert(0, self._get_assignment_action(quib, assignment, assignment_index))

            self._pending_undo_group = []
            self._undo_action_groups.append(pushing_undo_group)
            self._redo_action_groups.clear()
            self.set_undo_redo_buttons_enable_state()

    def _set_previous_assignment_action_for_quib_at_relevant_path(self,
                                                                  quib: Quib,
                                                                  path,
                                                                  previous_assignment_action:
                                                                  Optional[AddAssignmentAction]):
        """
        Set's the last released assignment action for a quib at that assignment's path.
         This is important as for every action we undo, we need to know to "where to return"- ie what was the last
         assignment at that path that we need to return to.
         We can't simply remove the assignment we want to undo because we may have *overwritten* another assignment
        """
        weak_ref = weakref.ref(quib, lambda k: self._quib_refs_to_paths_to_assignment_actions.pop(k))
        paths_to_released_assignments = self._quib_refs_to_paths_to_assignment_actions[weak_ref]
        from pyquibbler.path import get_hashable_path
        paths_to_released_assignments[
            get_hashable_path(path)
        ] = previous_assignment_action

    def _get_assignment_action(self, quib: Quib, assignment: Assignment, assignment_index: int):
        """
        Push a new assignment to the undo stack.
        """
        from pyquibbler.project import AddAssignmentAction
        from pyquibbler.path import get_hashable_path
        assignment_hashable_path = get_hashable_path(assignment.path)
        previous_assignment_action = self._quib_refs_to_paths_to_assignment_actions.get(weakref.ref(quib), {}).get(
            assignment_hashable_path
        )
        assignment_action = AddAssignmentAction(
            quib_ref=weakref.ref(quib, self.clear_undo_and_redo_stacks),
            assignment_index=assignment_index,
            assignment=assignment,
            previous_assignment_action=previous_assignment_action
        )
        self._set_previous_assignment_action_for_quib_at_relevant_path(quib, assignment.path, assignment_action)
        return assignment_action

    def upsert_assignment_to_quib(self, quib, index, assignment):
        self.push_single_assignment_to_undo_stack(
            quib=quib,
            assignment=assignment,
            assignment_index=index
        )
        if len(quib.handler.overrider) > index:
            old_assignment = quib.handler.overrider.pop_assignment_at_index(index)
        else:
            old_assignment = None
        quib.handler.overrider.insert_assignment_at_index(assignment, index)
        quib.handler.file_syncer.on_data_changed()
        quib.handler.invalidate_and_aggregate_redraw_at_path(assignment.path)
        if old_assignment is not None:
            quib.handler.invalidate_and_aggregate_redraw_at_path(old_assignment.path)
        quib.handler.on_overrides_changes()

    def remove_assignment_from_quib(self, quib: Quib, assignment_index: int):
        """
        Remove an assignment from the quib, ensuring that it will be able to be "undone" and "redone"
        should `undo`/`redo` be called
        """
        from pyquibbler.path import get_hashable_path

        assignment = quib.handler.overrider.pop_assignment_at_index(assignment_index)
        assignment_action = self._quib_refs_to_paths_to_assignment_actions[weakref.ref(quib)].get(
            get_hashable_path(assignment.path),
            AddAssignmentAction(
                assignment=assignment,
                assignment_index=assignment_index,
                previous_assignment_action=None,
                quib_ref=weakref.ref(quib)
            )
        )
        self._undo_action_groups.append([RemoveAssignmentAction(
            add_assignment_action=assignment_action,
            quib_ref=weakref.ref(quib)
        )])

        self._redo_action_groups.clear()
        quib.handler.file_syncer.on_data_changed()
        self.set_undo_redo_buttons_enable_state()

        quib.handler.invalidate_and_aggregate_redraw_at_path(assignment.path)
        quib.handler.on_overrides_changes()

    def notify_of_overriding_changes(self, quib: Quib):
        pass

    def set_undo_redo_buttons_enable_state(self):
        pass

    def text_dialog(self, title: str, message: str, buttons_and_options: Mapping[str, str]) -> str:
        print(title)
        print(message)
        for button, option in buttons_and_options.items():
            print(button, ': ', option)
        while True:
            choice = input()
            if choice in buttons_and_options.keys():
                return choice
