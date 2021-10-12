from __future__ import annotations
import numpy as np

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List, Union, Tuple, Type, Dict

if TYPE_CHECKING:
    from ..quib import Quib


@dataclass
class PathComponent:
    indexed_cls: Type
    component: Any

    def references_field_in_field_array(self):
        """
        Whether or not the component references a field in a field array
        It's important to note that this method is necessary as we need to dynamically decide whether a __setitem__
        assignment is a field assignment or not. This is in contrast to setattr for example where we could have had a
        special PathComponent for it, as the interface for setting an attribute is different.
        """
        return (
                issubclass(self.indexed_cls, np.ndarray) and
                (
                        isinstance(self.component, str) or
                        (isinstance(self.component, list) and isinstance(self.component[0], str))
                )
        )


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
    An assignment to be performed on a specific quib.
    """
    quib: Quib
    assignment: Assignment

    def apply(self) -> None:
        self.quib.assign(self.assignment)

    def override(self):
        self.quib.override(self.assignment, allow_overriding_from_now_on=False)
