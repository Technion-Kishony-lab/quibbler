from typing import Any, List, Optional, Iterable

from .assignment import Assignment
from .assignment_template import AssignmentTemplate
from ...exceptions import PyQuibblerException


class MixBetweenGlobalAndPartialOverridesException(PyQuibblerException):
    pass


class Overrider:
    """
    Gathers overriding assignments performed on a quib in order to apply them on a quib value.
    """

    def __init__(self, assignments: Iterable[Assignment] = ()):
        self._assignments: List[Assignment] = list(assignments)

    def add_assignment(self, assignment: Assignment):
        """
        Adds an override to the overrider - data[key] = value.
        """
        self._assignments.append(assignment)

    def override_collection(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Applies all overrides to the given data.
        """
        for assignment in self._assignments:
            if assignment.key is None:
                raise MixBetweenGlobalAndPartialOverridesException()
            assignment.apply(data, assignment_template)

    def is_global_override(self):
        """
        Returns whether the overrider's assignments represent a global override
        """
        return len(self._assignments) > 0 and all(assignment.key is None for assignment in self._assignments)

    def get_global_override(self, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Get's a single global overridden value
        If there's any overrides on specific indices we raise an exception since we will not be able to handle this as
        we are not changing any data
        """
        if any([assignment.key is not None for assignment in self._assignments]):
            raise MixBetweenGlobalAndPartialOverridesException()
        value = self._assignments[-1].value
        return value if assignment_template is None else assignment_template.convert(value)

    def __getitem__(self, item) -> Assignment:
        return self._assignments[item]

    def __repr__(self):
        return repr(self._assignments)
