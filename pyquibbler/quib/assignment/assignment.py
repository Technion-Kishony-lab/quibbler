from __future__ import annotations
import numpy as np

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List, Union, Tuple, Type, Dict

if TYPE_CHECKING:
    from ..quib import Quib


@dataclass
class PathComponent:
    cls: Type
    component: Any

    def references_field_in_field_array(self):
        return self.cls == np.ndarray and (isinstance(self.component, str)
                                           or
                                           (isinstance(self.component, list) and isinstance(self.component[0], str)))


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
        return np.array_equal((self.value, self.path), (other.value, other.path))


@dataclass(frozen=True)
class QuibWithAssignment:
    """
    A quib together with it's assignment
    """
    quib: Quib
    assignment: Assignment

    def apply(self) -> None:
        self.quib.assign(self.assignment)

    def override(self):
        self.quib.override(self.assignment, allow_overriding_from_now_on=False)
