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
    """
    An assignment whose value is known up to a given tolerance.
    Assignment-with-tolerance are created in graphics-driven assignments to reflect the resolution of the mouse event.
    These tolerances are then followed upstream as part of the process of inverse-assignment,
    allowing rounding the actual override to the correct number of significant digits.
    """

    # The upper and lower limits of the assignment value:
    value_up: Any = None
    value_down: Any = None

    def get_assignments_nominal_up_down(self):
        """
        Convert this AssignmentWithTolerance into 3 separate normal Assignments.
        """
        return \
            Assignment(self.value, self.path), \
            Assignment(self.value_up, self.path), \
            Assignment(self.value_down, self.path)

    def get_relative_error(self):
        return np.abs((self.value_up - self.value_down) / 2 / self.value)

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

    from .assignment_template import round_to_num_digits

    value = assignment.value
    try:
        relative_error = assignment.get_relative_error()
        num_digits = np.int64(np.ceil(-np.log10(relative_error)))
        value = round_to_num_digits(value, num_digits)
    except TypeError:
        pass

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
