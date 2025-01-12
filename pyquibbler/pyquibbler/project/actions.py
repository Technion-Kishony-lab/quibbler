from __future__ import annotations

from weakref import ReferenceType
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from pyquibbler.assignment import Assignment
from pyquibbler.quib.graphics.redraw import notify_of_overriding_changes_or_add_in_aggregate_mode

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
    assignment: Assignment
    next_assignment: Optional[Assignment]

    @property
    def quib(self) -> Quib:
        return self.quib_ref()

    def delete_assignment(self):
        self.quib.handler.overrider.pop_assignment_before_assignment(self.next_assignment)

    def add_assignment(self):
        self.quib.handler.overrider.add_new_assignment_before_assignment(self.assignment, self.next_assignment)

    def run_post_action(self):
        self.quib.handler.file_syncer.on_data_changed()
        self.quib.handler.invalidate_and_aggregate_redraw_at_path(self.assignment.path)
        notify_of_overriding_changes_or_add_in_aggregate_mode(self.quib)


class AddAssignmentAction(AssignmentAction):

    def _undo(self):
        self.delete_assignment()

    def _redo(self):
        self.add_assignment()


class RemoveAssignmentAction(AssignmentAction):

    def _undo(self):
        self.add_assignment()

    def _redo(self):
        self.delete_assignment()
