from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from pyquibbler.exceptions import PyQuibblerException

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_call import FuncCall


@dataclass
class FailedToTypeTranslateException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"Failed to translate type {self.func}"


@dataclass
class NoTypeTranslatorsWorkedException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"No type translator was found for {self.func}"
