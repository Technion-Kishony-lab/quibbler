from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List, Optional, Union

from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib import Quib
from pyquibbler.quib.assignment.overrider import AssignmentRemoval, Overrider


class Action(ABC):

    @abstractmethod
    def commit(self):
        pass


@dataclass
class AssignmentAction(Action):

    quib: Quib
    overrider: Overrider
    previous_index: int
    previous_assignment: Optional[Union[Assignment, AssignmentRemoval]]
    new_assignment: Union[Assignment, AssignmentRemoval]

    def commit(self):
        self.overrider.undo_assignment(assignment_to_return=self.previous_assignment,
                                       previous_path=self.new_assignment.path,
                                       previous_index=self.previous_index)
        self.quib.invalidate_and_redraw_at_path(self.new_assignment.path)


@dataclass
class ActionStack:
    actions: List[Action]

    def push(self, action: Action):
        self.actions.append(action)

    def pop_and_commit(self):
        last_action = self.actions.pop(-1)
        last_action.commit()
        return last_action


