import dataclasses
from typing import Callable

from pyquibbler.exceptions import PyQuibblerException


@dataclasses.dataclass
class CannotReverseUnknownFunctionException(PyQuibblerException):
    func: Callable
