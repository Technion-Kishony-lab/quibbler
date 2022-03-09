from __future__ import annotations
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List

from .exceptions import CannotReverseException
from pyquibbler.path.path_component import Path

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


@dataclass
class Assignment:
    """
    A change performed on a quib.
    """
    value: Any
    path: Path = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, Assignment):
            return NotImplemented
        # array_equal works for all objects, and our value and paths might contain ndarrays
        return np.array_equal(self.value, other.value) and np.array_equal(self.path, other.path)


@dataclass(frozen=True)
class QuibChange(ABC):
    quib: Quib

    @property
    @abstractmethod
    def path(self):
        """
        The path in which the quib is changed
        """

    @abstractmethod
    def apply(self) -> None:
        """
        Apply the change
        """


@dataclass(frozen=True)
class QuibWithAssignment(QuibChange, ABC):
    """
    An assignment to be performed on a specific quib.
    """
    assignment: Assignment

    @property
    def path(self):
        return self.assignment.path


class AssignmentToQuib(QuibWithAssignment):
    def apply(self) -> None:
        self.quib.apply_assignment(self.assignment)

    def to_override(self) -> Override:
        return Override(self.quib, self.assignment)

    def get_inversions(self, return_empty_list_instead_of_raising=False) -> List[AssignmentToQuib]:
        try:
            return self.quib.get_inversions_for_assignment(self.assignment)
        except CannotReverseException:
            if return_empty_list_instead_of_raising:
                return []
            raise


class Override(QuibWithAssignment):
    def apply(self) -> None:
        self.quib.override(self.assignment, allow_overriding_from_now_on=False)
