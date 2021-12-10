from dataclasses import dataclass
from enum import Enum
from typing import Any, Union

from pyquibbler.overriding.types import Argument


@dataclass(frozen=True)
class ArgumentWithValue:
    argument: Argument
    value: Any



class SourceType(Enum):
    DATA = 0
    PARAMETER = 1


@dataclass(frozen=True)
class Source:
    value: Any

    def __hash__(self):
        return hash(id(self))


@dataclass
class Inversal:
    assignment: Any
    source: Source
