from dataclasses import dataclass

from pyquibbler.assignment import AssignmentToQuib
from pyquibbler.exceptions import PyQuibblerException


@dataclass
class CannotChangeQuibAtPathException(PyQuibblerException):
    quib_change: AssignmentToQuib

    def __str__(self):
        return f'Cannot perform {self.quib_change.assignment} on {self.quib_change.quib}.\n' \
               f'The quib cannot be overridden and an overridable parent quib to inverse assign into was not found.\n' \
               f'Note that function quibs are not overridable by default.\n' \
               f'To allow overriding, try setting "{self.quib_change.quib}.allow_overriding = True"'


@dataclass
class AssignmentCancelledByUserException(PyQuibblerException):

    def __str__(self):
        return "User canceled inverse assignment dialog."
