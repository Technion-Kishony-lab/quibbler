from __future__ import annotations

import numpy as np
from dataclasses import dataclass, field
from typing import Any, List, Union, Optional, Callable, Tuple

from pyquibbler.utilities.numpy_original_functions import np_array
from pyquibbler.quib.pretty_converters.math_expressions.getitem_expression import GetItemExpression
from pyquibbler.path import Path, deep_get

from .default_value import default
from .rounding import floor_log10
from .utils import is_numeric_scalar
from .assignment_template import round_to_num_digits

from typing import TYPE_CHECKING
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
        return ''.join([str(GetItemExpression('', cmp.component)) for cmp in self.path])

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
        diff = (np_array(self.value_up) - np_array(self.value_down)) / 2
        relative_error = diff / np_array(self.value)
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

    if tolerance is None:
        if convert_func:
            value = convert_func(value)
        return Assignment(value, path)

    original_type = type(value)
    value_is_list_or_tuple = isinstance(value, (list, tuple))
    if value_is_list_or_tuple:
        value = np.array(value)

    value_up = value + tolerance
    value_down = value - tolerance

    if is_numeric_scalar(value) or value_is_list_or_tuple:
        value = original_type(value)
        value_up = original_type(value_up)
        value_down = original_type(value_down)

    if convert_func:
        value = convert_func(value)
        value_up = convert_func(value_up)
        value_down = convert_func(value_down)

    return AssignmentWithTolerance(value=value,
                                   path=path,
                                   value_up=value_up,
                                   value_down=value_down)


def create_assignment_from_nominal_down_up_values(nominal_down_up_values: Union[List, Tuple], path: Path):
    """
    Create Assignment or AssignmentWithTolerance
    If value_nominal_down_up is a len=3 tuple, use its values, as nominal, down, up, to create AssignmentWithTolerance.

    If value_nominal_down_up is a len=1 tuple, use its value as the nominal value for creating a regular Assignment.
    """
    assignment = Assignment(
        path=path,
        value=nominal_down_up_values[0]
    )
    if len(nominal_down_up_values) == 3:
        # assignment with tolerance:
        assignment = AssignmentWithTolerance.from_assignment_and_up_down_values(
            assignment=assignment,
            value_down=nominal_down_up_values[1],
            value_up=nominal_down_up_values[2],
        )
    return assignment


@dataclass(frozen=True)
class AssignmentToQuib:
    """
    Assignment to a specific quib can either `apply` locally as override or inverted to a list of
    assignments to upstream quibs.
    """
    quib: Quib
    assignment: Union[Assignment, AssignmentWithTolerance]

    def get_value_valid_at_path(self):
        return self.quib.get_value_valid_at_path(self.assignment.path)

    def get_value_at_path(self):
        return deep_get(self.get_value_valid_at_path(), self.assignment.path)

    def get_inversions(self) -> List[AssignmentToQuib]:
        return self.quib.handler.get_inversions_for_assignment(self.assignment)

    def apply(self) -> None:
        self.quib.handler.override(self.assignment)

    @classmethod
    def create_default(cls, quib: Quib, path: Path):
        return cls(quib, Assignment.create_default(path))
