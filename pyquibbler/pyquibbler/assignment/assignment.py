from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List, Union, Optional, Callable

from .default_value import default
from pyquibbler.path import Path
from .rounding import floor_log10
from ..quib.pretty_converters.pretty_convert import getitem_converter

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

    def get_pretty_path(self):
        return ''.join([str(getitem_converter(None, ('', cmp.component))) for cmp in self.path])

    def get_pretty_value(self):
        return repr(self.value)


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
    equal_number_of_digits: bool = True

    def get_assignments_nominal_up_down(self):
        """
        Convert this AssignmentWithTolerance into 3 separate normal Assignments.
        """
        return \
            Assignment(self.value, self.path), \
            Assignment(self.value_up, self.path), \
            Assignment(self.value_down, self.path)

    @np.errstate(divide='ignore', invalid='ignore')
    def get_relative_error(self):
        diff = (np.array(self.value_up) - np.array(self.value_down)) / 2
        relative_error = diff / np.array(self.value)
        return np.abs(relative_error)

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

    def get_pretty_assignment(self) -> Assignment:

        from .assignment_template import round_to_num_digits

        value = self.value
        try:
            relative_error = self.get_relative_error()
            num_digits = -floor_log10(relative_error)
            if self.equal_number_of_digits and isinstance(num_digits, np.ndarray):
                num_digits = max(num_digits)
            value = round_to_num_digits(value, num_digits)
        except TypeError:
            pass

        return Assignment(value=value, path=self.path)


def create_assignment(value: Any, path: Path,
                      tolerance: Optional[Any] = None,
                      convert_func: Optional[Callable] = None) -> Union[Assignment, AssignmentWithTolerance]:

    convert_func = convert_func if convert_func is not None else lambda x: x

    if tolerance is None:
        return Assignment(convert_func(value), path)

    value_numeric = np.array(value)
    tolerance_numeric = np.array(tolerance)
    value_up = type(value)(value_numeric + tolerance_numeric)
    value_down = type(value)(value_numeric - tolerance_numeric)

    return AssignmentWithTolerance(value=convert_func(value),
                                   path=path,
                                   value_up=convert_func(value_up),
                                   value_down=convert_func(value_down))


@dataclass(frozen=True)
class AssignmentToQuib:
    """
    Assignment to a specific quib can either `apply` locally as override or inverted to a list of
    assignments to upstream quibs.
    """
    quib: Quib
    assignment: Union[Assignment, AssignmentWithTolerance]

    def get_inversions(self, return_empty_list_instead_of_raising=False) -> List[AssignmentToQuib]:
        return self.quib.handler.get_inversions_for_assignment(self.assignment)

    def apply(self) -> None:
        self.quib.handler.override(self.assignment)

    @classmethod
    def create_default(cls, quib: Quib, path: Path):
        return cls(quib, Assignment.create_default(path))
