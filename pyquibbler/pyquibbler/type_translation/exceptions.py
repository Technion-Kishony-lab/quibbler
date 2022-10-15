from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

from pyquibbler.utilities.multiple_instance_runner import RunnerFailedException


@dataclass
class FailedToTypeTranslateException(RunnerFailedException):

    func: Callable

    def __str__(self):
        return f"Failed to translate type {self.func}"

