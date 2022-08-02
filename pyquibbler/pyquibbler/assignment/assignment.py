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

    def remove_class_from_path(self) -> Path:
        for component in self.path:
            component.indexed_cls = None
        return self.path

    @classmethod
    def create_default(cls, path: Path):
        return cls(default, path)


@dataclass
class AssignmentWithTolerance(Assignment):
    value_up: Any = None
    value_down: Any = None

    def get_assignments_nominal_up_down(self):
        return Assignment(self.value, self.path),\
               Assignment(self.value_up, self.path), \
               Assignment(self.value_down, self.path)

    def get_tolerance(self):
        return np.abs(self.value_up - self.value_down) / 2

    @classmethod
    def from_assignment_and_up_down_values(cls, assignment: Assignment,
                                           value_up: Any, value_down: Any):
        return cls(value=assignment.value,
                   path=assignment.path,
                   value_up=value_up,
                   value_down=value_down)

    @classmethod
    def from_value_path_tolerance(cls, value: Any, path: Path, tolerance: Any):
        return cls(value=value,
                   path=path,
                   value_up=value + tolerance,
                   value_down=value - tolerance)


def convert_assignment_with_tolerance_to_pretty_assignment(
        assignment: AssignmentWithTolerance) -> Assignment:

    relative_error = assignment.get_tolerance() / assignment.value
    num_digits = -np.log10(relative_error)

    # TODO: maybe better to round each value in the array with its own number rof digits
    num_digits = int(np.ceil(np.max(num_digits)))

    value = np.round(assignment.value, num_digits)
    return Assignment(value=value, path=assignment.path)


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
