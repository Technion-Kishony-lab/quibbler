from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import Optional, Union

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib import Quib
from pyquibbler.quib.assignment.overrider import AssignmentRemoval, Overrider


class Action(ABC):

    @abstractmethod
    def undo(self):
        pass


@dataclass
class AssignmentAction(Action):

    quib: Quib
    overrider: Overrider
    previous_index: int
    previous_assignment: Optional[Union[Assignment, AssignmentRemoval]]
    new_assignment: Union[Assignment, AssignmentRemoval]

    def undo(self):
        """
        Tell overrider to undo an assignment - see overrider docs for more info
        """
        self.overrider.undo_assignment(assignment_to_return=self.previous_assignment,
                                       previous_path=self.new_assignment.path,
                                       previous_index=self.previous_index)
        self.quib.invalidate_and_redraw_at_path(self.new_assignment.path)

    def redo(self):
        """
        Redo an undo
        """
        self.overrider.redo_assignment(previous_index=self.previous_index,
                                       assignment_to_return=self.new_assignment)
        self.quib.invalidate_and_redraw_at_path(self.new_assignment.path)
