from __future__ import annotations

from weakref import ReferenceType
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, Union, TYPE_CHECKING

from pyquibbler.assignment import Assignment, Overrider, AssignmentToDefault

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


class Action(ABC):

    @abstractmethod
    def undo(self):
        pass

    @abstractmethod
    def redo(self):
        pass


@dataclass
class AssignmentAction(Action):

    quib_ref: ReferenceType[Quib]
    overrider: Overrider
    assignment_index: int
    previous_assignment_action: Optional[AssignmentAction]
    assignment: Union[Assignment, AssignmentToDefault]

    @property
    def quib(self) -> Quib:
        return self.quib_ref()

    def undo(self):
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
            self.overrider.insert_assignment_at_path_and_index(
                assignment=self.previous_assignment_action.assignment,
                path=self.assignment.path,
                index=self.previous_assignment_action.assignment_index
            )

        self.quib.handler.file_syncer.on_data_changed()
        self.quib.handler.invalidate_and_redraw_at_path(self.assignment.path)

    def redo(self):
        """
        Redo an undo
        """
        self.overrider.pop_assignment_at_path(
            self.assignment.path,
            raise_on_not_found=False
        )
        self.overrider.insert_assignment_at_path_and_index(
            assignment=self.assignment,
            path=self.assignment.path,
            index=self.assignment_index
        )

        self.quib.handler.file_syncer.on_data_changed()
        self.quib.handler.invalidate_and_redraw_at_path(self.assignment.path)
