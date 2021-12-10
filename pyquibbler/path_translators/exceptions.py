from dataclasses import dataclass
from typing import Callable

from pyquibbler.exceptions import PyQuibblerException


class TranslationException(PyQuibblerException):
    pass


class CannotInvertException(TranslationException):
    pass


@dataclass
class NoInvertersFoundException(TranslationException):

    func: Callable

    def __str__(self):
        return f"No inverter classes found for {self.func}"
