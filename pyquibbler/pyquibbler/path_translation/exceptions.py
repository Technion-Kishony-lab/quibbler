from __future__ import annotations

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.utilities.multiple_instance_runner import BaseRunnerFailedException


class FailedToTranslateException(BaseRunnerFailedException):
    def __str__(self):
        return "Failed to translate func call"


class PyQuibblerRaggedArrayException(PyQuibblerException):
    def __str__(self):
        return 'Arrays of ragged arrays or lists are not supported.'
