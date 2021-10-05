from typing import Any, List, Optional, Iterable

from .assignment import Assignment, IndicesAssignment
from .assignment_template import AssignmentTemplate
from ..utils import deep_copy_without_quibs_or_artists


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
        Deep copies the argument and returns said data with applied overrides
        """
        data = deep_copy_without_quibs_or_artists(data)
        for assignment in self._assignments:
            value = assignment.value if assignment_template is None else assignment_template.convert(assignment.value)
            if isinstance(assignment, IndicesAssignment):
                data_to_set = data
                if assignment.field is not None:
                    data_to_set = data[assignment.field]
                data_to_set[assignment.indices] = value
            else:
                if assignment.field is not None:
                    data[assignment.field] = value
                else:
                    data = value

        return data

    def __getitem__(self, item) -> Assignment:
        return self._assignments[item]

    def __repr__(self):
        return repr(self._assignments)
