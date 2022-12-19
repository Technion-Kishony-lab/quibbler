from __future__ import annotations

from weakref import ReferenceType
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from pyquibbler.assignment import Assignment

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


class Action(ABC):

    def undo(self):
        self._undo()
        self.run_post_action()

    def redo(self):
        self._redo()
        self.run_post_action()

    @abstractmethod
    def _undo(self):
        pass

    @abstractmethod
    def _redo(self):
        pass

    def run_post_action(self):
        pass


@dataclass
class AssignmentAction(Action, ABC):
    quib_ref: ReferenceType[Quib]
    assignment_index: int
    assignment: Assignment

    @property
    def quib(self) -> Quib:
        return self.quib_ref()

    def pop_assignment_at_index(self):
        self.quib.handler.overrider.pop_assignment_at_index(self.assignment_index)

    def insert_assignment_at_index(self):
        self.quib.handler.overrider.insert_assignment_at_index(self.assignment, self.assignment_index)

    def run_post_action(self):
        self.quib.handler.file_syncer.on_data_changed()
        self.quib.handler.invalidate_and_aggregate_redraw_at_path(self.assignment.path)
        self.quib.handler.on_overrides_changes()


@dataclass
class AddAssignmentAction(AssignmentAction):

    def _undo(self):
        self.pop_assignment_at_index()

    def _redo(self):
        self.insert_assignment_at_index()


@dataclass
class RemoveAssignmentAction(AssignmentAction):

    def _undo(self):
        self.insert_assignment_at_index()

    def _redo(self):
        self.pop_assignment_at_index()
