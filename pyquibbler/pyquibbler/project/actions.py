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

    @property
    def quib(self) -> Quib:
        return self.quib_ref()

    @property
    def overrider(self):
        return self.quib.handler.overrider

    @property
    @abstractmethod
    def relevant_path(self):
        pass

    def run_post_action(self):
        self.quib.handler.file_syncer.on_data_changed()
        self.quib.handler.invalidate_and_aggregate_redraw_at_path(self.relevant_path)


@dataclass
class AddAssignmentAction(AssignmentAction):

    assignment_index: int
    assignment: Assignment
    previous_assignment_action: Optional[AddAssignmentAction]

    @property
    def relevant_path(self):
        return self.assignment.path

    def _undo(self):
        """
        Undo an assignment, returning the overrider to the previous state before the assignment.
        Note that this is essentially different than simply adding an AssignmentRemoval ->
        if I do
        ```
        q = iquib(0)
        q.assign(1)
        q.assign(2)
        ```
        and then do return_assignments_to_default, the value will go back to 0 (the original value).
        if I do undo_assignment, the value will go back to 1 (the previous value)

        This also is necessarily NOT just removing the assignment, as we may have overwritten another assignment if
        we were on the same path
        """
        self.overrider.pop_assignment_at_path(self.assignment.path)
        if self.previous_assignment_action:
            self.overrider.insert_assignment_at_index(
                assignment=self.previous_assignment_action.assignment,
                index=self.previous_assignment_action.assignment_index
            )

    def _redo(self):
        """
        Redo an undo
        """
        self.overrider.pop_assignment_at_path(
            self.assignment.path,
            raise_on_not_found=False
        )
        self.overrider.insert_assignment_at_index(
            assignment=self.assignment,
            index=self.assignment_index
        )


@dataclass
class RemoveAssignmentAction(AssignmentAction):

    add_assignment_action: Optional[AddAssignmentAction]

    @property
    def relevant_path(self):
        return self.add_assignment_action.assignment.path

    def _undo(self):
        self.quib.handler.overrider.insert_assignment_at_index(self.add_assignment_action.assignment,
                                                               self.add_assignment_action.assignment_index)

    def _redo(self):
        self.quib.handler.overrider.pop_assignment_at_index(self.add_assignment_action.assignment_index)
