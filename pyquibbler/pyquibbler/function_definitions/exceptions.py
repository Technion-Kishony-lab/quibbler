from typing import Callable
from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException


@dataclass
class CannotFindDefinitionForFuncException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"There exists no overriding definition for `{self.func}`. Consider adding one!"
