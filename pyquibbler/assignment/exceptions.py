from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException


if TYPE_CHECKING:
    from pyquibbler import Assignment
    from pyquibbler.quib import Quib
    from pyquibbler.path import Path


@dataclass
class CannotReverseException(PyQuibblerException):
    function_quib: Quib
    assignment: Assignment


@dataclass
class CannotReverseUnknownFuncException(CannotReverseException):
    def __str__(self):
        return f'Reverse assignment is not implemented for {self.function_quib.func}'


class CommonAncestorBetweenArgumentsException(CannotReverseException):
    pass


@dataclass
class NoAssignmentFoundAtPathException(PyQuibblerException):
    path: Path
