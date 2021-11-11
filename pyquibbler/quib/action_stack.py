from abc import abstractmethod, ABC
from dataclasses import dataclass
from typing import List


class Action(ABC):

    @abstractmethod
    def commit(self):
        pass


@dataclass
class ActionStack:
    actions: List[Action]

    def push(self, action: Action):
        self.actions.append(action)

    def pop_and_commit(self):
        last_action = self.actions.pop(-1)
        last_action.commit()
        return last_action


