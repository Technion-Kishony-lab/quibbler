from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List, Optional, Union

from pyquibbler.exceptions import PyQuibblerException
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
        self.overrider.undo_assignment(assignment_to_return=self.previous_assignment,
                                       previous_path=self.new_assignment.path,
                                       previous_index=self.previous_index)
        self.quib.invalidate_and_redraw_at_path(self.new_assignment.path)

    def redo(self):
        self.overrider.redo_assignment(previous_index=self.previous_index,
                                       assignment_to_return=self.new_assignment)


@dataclass
class ActionStack(ABC):
    actions: List[Action]

    def push(self, action: Action):
        self.actions.append(action)

    @abstractmethod
    def commit_action(self, action):
        pass

    def pop_and_undo(self):
        try:
            last_action = self.actions.pop(-1)
        except IndexError:
            raise NothingToUndoException() from None
        self.commit_action(last_action)
        return last_action


class UndoStack(ActionStack):

    def commit_action(self, action):
        action.undo()


class UndoStack(ActionStack):

    def commit_action(self, action):
        action.undo()
