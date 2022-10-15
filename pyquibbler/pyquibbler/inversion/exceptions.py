from __future__ import annotations
from dataclasses import dataclass

from typing import TYPE_CHECKING

from pyquibbler.utilities.multiple_instance_runner import RunnerFailedException

if TYPE_CHECKING:
    from pyquibbler.function_definitions.func_call import FuncCall


@dataclass
class FailedToInvertException(RunnerFailedException):

    func_call: FuncCall

    def __str__(self):
        return f"Failed to invert {self.func_call}"

