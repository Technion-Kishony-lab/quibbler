from typing import Any, List, Optional, Iterable

from .assignment import Assignment
from .assignment_template import AssignmentTemplate


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

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Applies all overrides to the given data.
        """
        for assignment in self._assignments:
            assignment.apply(data, assignment_template)

    def __getitem__(self, item) -> Assignment:
        return self._assignments[item]

    def __repr__(self):
        return repr(self._assignments)
