from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Callable

from pyquibbler.exceptions import PyQuibblerException


class TranslationException(ABC, PyQuibblerException):
    pass


@dataclass
class FailedToTranslateException(TranslationException):

    def __str__(self):
        return "Failed to translate func call"


@dataclass
class NoTranslatorsFoundException(PyQuibblerException):

    func: Callable

    def __str__(self):
        return f"No translator was found for {self.func}"


class PyQuibblerRaggedArrayException(PyQuibblerException):
    def __str__(self):
        return 'Arrays of ragged arrays or lists are not supported.'
