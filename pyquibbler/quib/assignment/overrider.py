from typing import Any, List, Optional, Iterable

from .assignment import Assignment, ReplaceObject, AssignmentPath
from .assignment_template import AssignmentTemplate
from ..utils import deep_copy_without_quibs_or_artists


def _deep_assign_data_with_paths(data: Any, paths: List[AssignmentPath], value: Any):
    """
    Go path by path setting value, each time ensuring we don't lost copied values (for example if there was
    fancy indexing) by making sure to set recursively back anything that made an assignment
    """
    current_path = paths[0]
    if current_path is ReplaceObject:
        return value
    elif len(paths) == 1:
        data[current_path] = value
        return data

    data[current_path] = _deep_assign_data_with_paths(data[current_path], paths[1:], value)
    return data


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
            data = _deep_assign_data_with_paths(data, assignment.paths, value)

        return data

    def __getitem__(self, item) -> Assignment:
        return self._assignments[item]

    def __repr__(self):
        return repr(self._assignments)
