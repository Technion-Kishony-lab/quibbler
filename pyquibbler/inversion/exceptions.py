from dataclasses import dataclass

from typing import Callable

from pyquibbler.exceptions import PyQuibblerException


class CannotInvertException(PyQuibblerException):
    pass


@dataclass
class NoInvertersFoundException(CannotInvertException):

    func: Callable

    def __str__(self):
        return f"No inverter classes found for {self.func}"
