from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING

from pyquibbler.refactor.func_call import FuncCall
from pyquibbler.refactor.quib.utils import copy_and_convert_args_and_kwargs_to_values

if TYPE_CHECKING:
    from pyquibbler.refactor.overriding import Argument


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
