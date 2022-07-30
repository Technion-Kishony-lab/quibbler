from __future__ import annotations
import numpy as np
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List
from .default_value import default

from pyquibbler.path.path_component import Path

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


@dataclass
class Assignment:
    """
    A change to be performed on a quib.

    value=default indicates an assignment which sets the value back to default.
    """

    value: Any
    path: Path = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, Assignment):
            return NotImplemented
        # array_equal works for all objects, and our value and paths might contain ndarrays
        return np.array_equal(self.value, other.value) and np.array_equal(self.path, other.path)

    def is_default(self) -> bool:
        return self.value is default

    @classmethod
    def create_default(cls, path: Path):
        return cls(default, path)


@dataclass(frozen=True)
class AssignmentToQuib:
    """
    Assignment to a specific quib can either `apply` locally as override or inverted to a list of
    assignments to upstream quibs.
    """
    quib: Quib
    assignment: Assignment

    def get_inversions(self, return_empty_list_instead_of_raising=False) -> List[AssignmentToQuib]:
        return self.quib.handler.get_inversions_for_assignment(self.assignment)

    def apply(self) -> None:
        self.quib.handler.override(self.assignment)

    @classmethod
    def create_default(cls, quib: Quib, path: Path):
        return cls(quib, Assignment.create_default(path))
