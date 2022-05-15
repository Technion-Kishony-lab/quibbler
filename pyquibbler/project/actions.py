from __future__ import annotations

from weakref import ReferenceType
from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, Union, TYPE_CHECKING

from pyquibbler.assignment import Assignment, Overrider, AssignmentRemoval

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
    previous_index: int
    previous_assignment: Optional[Union[Assignment, AssignmentRemoval]]
    new_assignment: Union[Assignment, AssignmentRemoval]

    @property
    def quib(self) -> Quib:
        return self.quib_ref()

    def undo(self):
        """
        Tell overrider to undo an assignment - see overrider docs for more info
        """
        self.overrider.undo_assignment(assignment_to_return=self.previous_assignment,
                                       previous_path=self.new_assignment.path,
                                       previous_index=self.previous_index)
        self.quib.handler.file_syncer.on_data_changed()
        self.quib.handler.invalidate_and_redraw_at_path(self.new_assignment.path)

    def redo(self):
        """
        Redo an undo
        """
        self.overrider.redo_assignment(previous_index=self.previous_index,
                                       assignment_to_return=self.new_assignment)
        self.quib.handler.file_syncer.on_data_changed()
        self.quib.handler.invalidate_and_redraw_at_path(self.new_assignment.path)
