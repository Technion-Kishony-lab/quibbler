from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from pyquibbler.exceptions import PyQuibblerException

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_call import FuncCall


class TranslationException(PyQuibblerException):
    pass


@dataclass
class FailedToTranslateException(TranslationException):

    func_call: FuncCall

    def __str__(self):
        return f"Failed to translate {self.func_call}"


@dataclass
class NoTranslatorsFoundException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"No translator was found for {self.func}"
