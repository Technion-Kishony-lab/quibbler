from dataclasses import dataclass
from typing import Callable

from pyquibbler.exceptions import PyQuibblerException


class TranslationException(PyQuibblerException):
    pass
