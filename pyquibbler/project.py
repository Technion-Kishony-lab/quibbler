from __future__ import annotations

import contextlib
import weakref
from _weakref import ReferenceType
from pathlib import Path
import sys
from typing import Optional, Set, TYPE_CHECKING, List

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib.actions import Action, AssignmentAction
from pyquibbler.quib.assignment.assignment import get_hashable_path

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
        return "The current project does not have a path. Set one in order to save."


class CannotLoadWithoutProjectPathException(PyQuibblerException):

    def __str__(self):
        return "The current project does not have a path. Set one in order to load."


class Project:
    """
    A "quibbler" project, giving an interface to get globally collected information (such as all quibs created) and
    performing actions aggregatively on many quibs
    """

    current_project = None

    def __init__(self, path: Optional[Path], quib_weakrefs: Set[ReferenceType[Quib]]):
        self.path = path
        self._quib_weakrefs = quib_weakrefs
        self._pushing_undo_group = None
        self._undo_action_groups: List[List[Action]] = []
        self._redo_action_groups: List[List[Action]] = []
        self._quibs_to_paths_to_released_assignments = {}

    @classmethod
    def get_or_create(cls, path: Optional[Path] = None):
        if cls.current_project is None:
            main_module = sys.modules['__main__']
            path = path or (Path(main_module.__file__).parent if hasattr(main_module, '__file__') else None)
            cls.current_project = cls(path=path, quib_weakrefs=set())
        return cls.current_project

    @contextlib.contextmanager
    def start_undo_group(self):
        self._pushing_undo_group = []
        yield
        if self._pushing_undo_group:
            self._undo_action_groups.append(self._pushing_undo_group)
        self._pushing_undo_group = None

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

    @property
    def input_quib_directory(self) -> Optional[Path]:
        return self.path / "input_quibs" if self.path else None

    @property
    def function_quib_directory(self) -> Optional[Path]:
        return self.path / "function_quibs" if self.path else None

    def register_quib(self, quib: Quib):
        """
        Register a quib to the project
        """
        self._quib_weakrefs.add(weakref.ref(quib))

    def reset_invalidate_and_redraw_all_impure_function_quibs(self):
        """
        Reset and then invalidate_redraw all impure function quibs in the project.
        We do this aggregatively so as to ensure we don't redraw axes more than once
        """
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        from pyquibbler.quib import ImpureFunctionQuib
        impure_function_quibs = [quib for quib in self.quibs if isinstance(quib, ImpureFunctionQuib)]
        with aggregate_redraw_mode():
            for function_quib in impure_function_quibs:
                function_quib.reset_cache()
                function_quib.invalidate_and_redraw_at_path([])

    def save_quibs(self, save_iquibs_as_txt_where_possible: bool = True):
        """
        Save quibs (where relevant) to files in the current project directory
        """
        from pyquibbler.quib.input_quib import InputQuib, CannotSaveAsTextException
        if self.path is None:
            raise CannotSaveWithoutProjectPathException()
        for quib in self.quibs:
            if save_iquibs_as_txt_where_possible and isinstance(quib, InputQuib) and quib.allow_overriding:
                try:
                    quib.save_as_txt()
                except CannotSaveAsTextException:
                    pass
                else:
                    continue

            quib.save_if_relevant()

    def load_quibs(self):
        """
        Load quibs (where relevant) from files in the current project directory
        """
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        if self.path is None:
            raise CannotLoadWithoutProjectPathException()
        with aggregate_redraw_mode():
            for quib in self.quibs:
                quib.load()

    def has_undo(self):
        """
        Whether or not an undo exists
        """
        return len(self._undo_action_groups) > 0

    def has_redo(self):
        """
        Whether or not a redo exists
        """
        return len(self._redo_action_groups) > 0

    def _set_quib(self, action):
        self._quibs_to_paths_to_released_assignments.setdefault(action.quib, {})
        self._quibs_to_paths_to_released_assignments[action.quib][get_hashable_path(action.previous_assignment.path)] = \
            action.previous_assignment

    def undo(self):
        """
        Undo the last action committed (see overrider docs for more information)
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
                    if action.previous_assignment:
                        self._quibs_to_paths_to_released_assignments.setdefault(action.quib, {})
                        self._quibs_to_paths_to_released_assignments[action.quib][get_hashable_path(action.previous_assignment.path)] = \
                            action.previous_assignment
        self._redo_action_groups.append(actions)

    def redo(self):
        """
        Redo the last action committed
        """
        from pyquibbler.quib.graphics.redraw import aggregate_redraw_mode
        try:
            actions = self._redo_action_groups.pop(-1)
        except IndexError:
            raise NothingToRedoException() from None

        with aggregate_redraw_mode():
            for action in actions:
                action.redo()
                if isinstance(action, AssignmentAction):
                    self._quibs_to_paths_to_released_assignments.setdefault(action.quib, {})
                    self._quibs_to_paths_to_released_assignments[action.quib][get_hashable_path(action.new_assignment.path)] = \
                        action.new_assignment

        self._undo_action_groups.append(actions)

    def push_assignment_to_undo_stack(self, quib, overrider, assignment, index):
        from pyquibbler.quib.actions import AssignmentAction
        assignment_action = AssignmentAction(
            quib=quib,
            overrider=overrider,
            previous_index=index,
            new_assignment=assignment,
            previous_assignment=self._quibs_to_paths_to_released_assignments.get(quib, {}).get(get_hashable_path(assignment.path))
        )
        self._quibs_to_paths_to_released_assignments.setdefault(quib, {})[get_hashable_path(assignment.path)] = assignment
        # self._quibs_to_paths_to_released_assignments[quib] = assignment
        if self._pushing_undo_group is not None:
            self._pushing_undo_group.insert(0, assignment_action)
        else:
            self._undo_action_groups.append([assignment_action])

    def redraw_central_refresh_graphics_function_quibs(self):
        """
        Redraw all graphics function quibs which only redraw when set to UpdateType.CENTRAL
        """
        from pyquibbler.quib import GraphicsFunctionQuib, UpdateType
        for quib in self.quibs:
            if isinstance(quib, GraphicsFunctionQuib) and quib.update_type == UpdateType.CENTRAL:
                quib.get_value()
