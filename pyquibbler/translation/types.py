from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pyquibbler.function_definitions.types import Argument


@dataclass(frozen=True)
class ArgumentWithValue:
    argument: Argument
    value: Any


class SourceType(Enum):
    DATA = 0
    PARAMETER = 1


@dataclass
class Source:
    value: Any

    def __hash__(self):
        return hash(id(self))


@dataclass
class Inversal:
    assignment: Any
    source: Source
