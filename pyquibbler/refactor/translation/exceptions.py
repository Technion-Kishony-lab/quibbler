from dataclasses import dataclass
from typing import Callable

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.refactor.function_definitions.func_call import FuncCall


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

