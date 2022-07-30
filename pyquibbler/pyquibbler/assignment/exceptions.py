from __future__ import annotations
from typing import TYPE_CHECKING
from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException


if TYPE_CHECKING:
    from pyquibbler import Assignment
    from pyquibbler.quib import Quib
    from pyquibbler.path import Path


@dataclass
class NoAssignmentFoundAtPathException(PyQuibblerException):
    path: Path

    def __str__(self):
        return 'Attempting to remove an overriding assignment which does not exist.'
