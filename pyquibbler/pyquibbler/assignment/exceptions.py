from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException


if TYPE_CHECKING:
    from pyquibbler.path import Path


@dataclass
class NoAssignmentFoundAtPathException(PyQuibblerException):
    path: Path

    def __str__(self):
        return 'Attempting to remove an overriding assignment which does not exist.'


@dataclass
class CannotConvertTextToAssignmentsException(PyQuibblerException):
    text: str

    def __str__(self):
        return f'Failed loading assignments from file: {self.text}'


@dataclass
class CannotConvertAssignmentsToTextException(PyQuibblerException):

    def __str__(self):
        return "The quib assignments contain objects that cannot be converted to text." \
               "To save the quib, set the save_format to binary (quib.save_format = 'bin')."
