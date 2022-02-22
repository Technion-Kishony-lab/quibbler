from __future__ import annotations

import contextlib
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
from pyquibbler.quib.graphics import UpdateType
from pyquibbler.quib.save_assignments import SaveFormat

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class NothingToUndoException(PyQuibblerException):

    def __str__(self):
        return "There are no actions left to undo"


class NothingToRedoException(PyQuibblerException):

    def __str__(self):
        return "There are no actions left to redo"


class CannotSaveWithoutProjectPathException(PyQuibblerException):

    def __str__(self):
        return "The current project does not have a path. To save quibs, set a path first (see set_project_path)."


class CannotLoadWithoutProjectPathException(PyQuibblerException):

    def __str__(self):
        return "The current project does not have a path. To load quibs, set a path first (see set_project_path)."


class Project:
    """
    A "quibbler" project, giving an interface to get globally collected information (such as all quibs created) and
    performing actions aggregatively on many quibs
    """

    current_project = None

    def __init__(self, directory: Optional[Path], quib_weakrefs: Set[ReferenceType[Quib]]):
        self._directory = directory
        self._quib_weakrefs = quib_weakrefs
        self._pushing_undo_group = None
        self._undo_action_groups: List[List[Action]] = []
        self._redo_action_groups: List[List[Action]] = []
        self._quib_refs_to_paths_to_released_assignments = defaultdict(dict)
        self._save_format: SaveFormat = SaveFormat.TXT
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
        Get all quibs in the project that are still alive
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

    def _reset_list_of_quibs(self, quibs):
        # We aggregate to ensure we don't redraw axes more than once
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        with aggregate_redraw_mode():
            for function_quib in quibs:
                function_quib._invalidate_self([])
                function_quib.invalidate_and_redraw_at_path([])

    """
    central quib commands
    """

    def reset_random_quibs(self):
        """
        Reset and then invalidate_redraw all random quibs in the project.
        """
        self._reset_list_of_quibs([quib for quib in self.quibs if quib.is_random_func])


    def reset_impure_quibs(self):
        """
        Reset and then invalidate_redraw all impure quibs in the project.
        """
        self._reset_list_of_quibs([quib for quib in self.quibs if quib.is_impure])


    def redraw_central_refresh_graphics_function_quibs(self):
        """
        Redraw all graphics function quibs which only redraw when set to UpdateType.CENTRAL
        """
        for quib in self.quibs:
            if quib.redraw_update_type == UpdateType.CENTRAL:
                quib.get_value()

    """
    save/load
    """

    @property
    def directory(self) -> PathWithHyperLink:
        """
        The directory to which quibs are saved.

        Returns a Path object

        Can be set as a str or Path object.

        path = None indicates undefined path.
        """
        return PathWithHyperLink(self._directory)

    @directory.setter
    @validate_user_input(path=(type(None), str, Path))
    def directory(self, path: Optional[Path]):
        if isinstance(path, str):
            path = Path(path)
        self._directory = None if path is None else path.resolve()

        if self.on_path_change:
            self.on_path_change(path)

    @property
    def save_format(self) -> SaveFormat:
        """
        The default file format for saving quibs.

        Quibs whose own save_as_text is None yield to the default save_as_text of the Project.

        Returns:
             SaveFormat

        See also:
            Quib.save_format
        """
        return self._save_format

    @save_format.setter
    @validate_user_input(save_format=SaveFormat)
    def save_format(self, save_format: SaveFormat):
        self._save_format = save_format

    def save_quibs(self, save_as_txt_where_possible: bool = True):
        """
        Save all the quibs to files (if relevant- i.e. if they have overrides)

        save_as_txt: bool indicating whether each quib should try to save as text if possible.
            None (default) - respects each quib save_as_txt.
        """
        if self.directory is None:
            raise CannotSaveWithoutProjectPathException()
        for quib in self.quibs:
            quib.save()

    def load_quibs(self):
        """
        Load quibs (where relevant) from files in the current project directory.
        """
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        if self.directory is None:
            raise CannotLoadWithoutProjectPathException()
        with aggregate_redraw_mode():
            for quib in self.quibs:
                quib.load()

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
        Whether or not an assignment undo exists.

        Returns: bool
        """
        return len(self._undo_action_groups) > 0

    def can_redo(self):
        """
        Whether or not an assignment redo exists

        Returns: bool
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
        Undo the last quib assignment (see overrider docs for more information)
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
        Redo the last quib assignment
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

    def _clear_undo_and_redo_stacks(self, *_, **__):
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
            quib_ref=weakref.ref(quib, self._clear_undo_and_redo_stacks),
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
