from __future__ import annotations

from dataclasses import dataclass

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.utilities.multiple_instance_runner import RunnerFailedException


@dataclass
class FailedToTranslateException(RunnerFailedException):

    def __str__(self):
        return "Failed to translate func call"


class PyQuibblerRaggedArrayException(PyQuibblerException):
    def __str__(self):
        return 'Arrays of ragged arrays or lists are not supported.'
