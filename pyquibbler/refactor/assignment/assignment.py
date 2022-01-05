from __future__ import annotations
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List

from .exceptions import CannotReverseException
from pyquibbler.refactor.path.path_component import PathComponent

if TYPE_CHECKING:
    from pyquibbler.refactor.quib.quib import Quib


@dataclass
class Assignment:
    """
    A change performed on a quib.
    """
    value: Any
    path: List[PathComponent] = field(default_factory=list)

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
        self.quib.assign(self.assignment)

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


@dataclass(frozen=True)
class FrozenSlice:
    start: int
    step: int
    stop: int


def _hash_component_value(inner_component):
    if isinstance(inner_component, list):
        return tuple([_hash_component_value(x) for x in inner_component])
    elif isinstance(inner_component, np.ndarray):
        return inner_component.tobytes()
    elif isinstance(inner_component, slice):
        return FrozenSlice(inner_component.start, inner_component.step, inner_component.stop)
    elif isinstance(inner_component, tuple):
        return tuple([_hash_component_value(x) for x in inner_component])
    return inner_component


def get_hashable_path(path: List[PathComponent]):
    """
    Get a hashable path (list of pathcomponents)- this supports known indexing methods
    """
    return tuple([
        _hash_component_value(p.component) for p in path
    ])
