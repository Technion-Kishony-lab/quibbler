from typing import Any, List, Optional

from .assignment import Assignment
from .assignment_template import AssignmentTemplate


class Overrider:
    def __init__(self):
        self._assignments: List[Assignment] = []

    def add_assignment(self, key: Any, value: Any):
        """
        Adds an override to the overrider - data[key] = value.
        """
        self._assignments.append(Assignment(key, value))

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Applies all overrides to the given data.
        """
        for assignment in self._assignments:
            assignment.apply(data, assignment_template)

    def __getitem__(self, item) -> Assignment:
        return self._assignments[item]
