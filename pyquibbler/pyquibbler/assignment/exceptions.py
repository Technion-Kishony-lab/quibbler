from __future__ import annotations
from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException


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
