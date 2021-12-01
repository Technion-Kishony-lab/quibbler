from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyquibbler import Assignment
from pyquibbler.exceptions import PyQuibblerException

if TYPE_CHECKING:
    from pyquibbler.quib.refactor.quib import Quib


@dataclass
class OverridingNotAllowedException(PyQuibblerException):
    quib: Quib
    override: Assignment

    def __str__(self):
        return f'Cannot override {self.quib} with {self.override} as it does not allow overriding.'


@dataclass
class UnknownUpdateTypeException(PyQuibblerException):
    attempted_update_type: str

    def __str__(self):
        return f"{self.attempted_update_type} is not a valid update type"

