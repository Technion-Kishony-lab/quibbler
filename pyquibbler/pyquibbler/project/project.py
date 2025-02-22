from __future__ import annotations

import weakref

from pathlib import Path
import sys
from typing import Optional, Set, List, Callable, Union, Mapping

from pyquibbler.utilities.input_validation_utils import get_enum_by_str, validate_user_input
from pyquibbler.utilities.file_path import PathWithHyperLink
from pyquibbler.quib.graphics import GraphicsUpdateType, aggregate_redraw_mode
from pyquibbler.file_syncing.types import SaveFormat, ResponseToFileNotDefined

from .actions import AssignmentAction, AddAssignmentAction, RemoveAssignmentAction
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
        self._pending_undo_group: Optional[List[AssignmentAction]] = None
        self._undo_action_groups: List[List[AssignmentAction]] = []
        self._redo_action_groups: List[List[AssignmentAction]] = []
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
            for action in actions[-1::-1]:
                action.undo()

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

        self._undo_action_groups.append(actions)
        self.set_undo_redo_buttons_enable_state()

    def clear_undo_and_redo_stacks(self, *_, **__):
        """clear_undo_and_redo_stacks()

        Clear the undo/redo stack.

        See Also
        --------
        undo, redo, can_undo, can_redo
        """
        self._undo_action_groups.clear()
        self._redo_action_groups.clear()
        self.set_undo_redo_buttons_enable_state()

    def start_pending_undo_group(self):
        self._pending_undo_group = []

    def undo_pending_group(self, temporarily: bool = False):
        actions = self._pending_undo_group
        with aggregate_redraw_mode(temporarily):
            for action in actions[-1::-1]:
                action.undo()
        self.start_pending_undo_group()

    def upsert_assignment_to_pending_undo_group(self,
                                                quib: Quib,
                                                assignment: Optional[Assignment] = None,
                                                next_assignment: Optional[Assignment] = None,
                                                old_assignment: Optional[Assignment] = None,
                                                old_next_assignment: Optional[Assignment] = None):
        quib_ref = weakref.ref(quib, self.clear_undo_and_redo_stacks)
        if old_assignment:
            self._pending_undo_group.append(
                RemoveAssignmentAction(quib_ref=quib_ref,
                                       assignment=old_assignment,
                                       next_assignment=old_next_assignment)
            )
        if assignment:
            self._pending_undo_group.append(
                AddAssignmentAction(quib_ref=quib_ref,
                                    assignment=assignment,
                                    next_assignment=next_assignment)
            )

    def squash_pending_group_into_last_undo(self):
        """
        Combine the pending group into the last undo group while removing Add-Remove action pairs acting on
        the same assignment.
        """
        actions = self._undo_action_groups.pop(-1)
        actions.extend(self._pending_undo_group)
        self._pending_undo_group = []
        remove_index = 1
        while remove_index < len(actions):
            remove_action = actions[remove_index]
            if isinstance(remove_action, RemoveAssignmentAction):
                for add_index in range(remove_index - 1, -1, -1):
                    add_action = actions[add_index]
                    if isinstance(add_action, AddAssignmentAction) \
                            and add_action.assignment is remove_action.assignment:
                        # need to change the "next_assignment" pointers of assignments that pointed to the one we delete
                        for action in actions[add_index + 1:remove_index]:
                            if action.next_assignment is add_action.assignment:
                                action.next_assignment = add_action.next_assignment
                        del actions[remove_index]
                        del actions[add_index]
                        remove_index -= 2
                        break
            remove_index += 1
        self._undo_action_groups.append(actions)
        self._redo_action_groups.clear()

    def push_empty_group_to_undo_stack(self):
        self._undo_action_groups.append([])

    def remove_last_undo_group_if_empty(self):
        while len(self._undo_action_groups) > 0 and len(self._undo_action_groups[-1]) == 0:
            self._undo_action_groups.pop(-1)

    def push_pending_undo_group_to_undo_stack(self):
        if not self._pending_undo_group:
            return
        self._undo_action_groups.append(self._pending_undo_group)
        self._pending_undo_group = []
        self._redo_action_groups.clear()
        self.set_undo_redo_buttons_enable_state()

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
