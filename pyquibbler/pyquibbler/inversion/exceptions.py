from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
from typing import Callable

from pyquibbler.exceptions import PyQuibblerException

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_call import FuncCall


@dataclass
class FailedToInvertException(PyQuibblerException):

    func_call: FuncCall

    def __str__(self):
        return f"Failed to invert {self.func_call}"


@dataclass
class NoInvertersFoundException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"No inverter was found for {self.func}"
