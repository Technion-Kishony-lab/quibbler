from __future__ import annotations
from dataclasses import dataclass
from typing import Set, Any

from pyquibbler.exceptions import PyQuibblerException, DebugException

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


@dataclass
class NestedQuibException(DebugException):
    obj: Any
    nested_quibs: Set[Quib]

    def __str__(self):
        return 'PyQuibbler does not support calling functions with arguments that contain deeply nested quibs.\n' \
               f'The quibs {self.nested_quibs} are deeply nested within {self.obj}.'


@dataclass
class CannotLoadAssignmentsFromTextException(PyQuibblerException):
    file: str

    def __str__(self):
        return f'Failed loading assignments from file: {self.file}'


@dataclass
class CannotSaveAssignmentsAsTextException(PyQuibblerException):

    def __str__(self):
        return "The quib assignments contain objects that cannot be saved as text." \
               "To save the quib, set the save_format to binary (quib.save_format = 'bin')."
