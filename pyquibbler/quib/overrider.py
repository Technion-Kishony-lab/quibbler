from typing import Any, Tuple, List, Optional

from .assignment_template import AssignmentTemplate


class Overrider:
    def __init__(self):
        self._overrides: List[Tuple[Any, Any]] = []

    def add_override(self, key: Any, value: Any):
        """
        Adds an override to the overrider - data[key] = value.
        """
        self._overrides.append((key, value))

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Applies all overrides to the given data.
        """
        for key, value in self._overrides:
            if assignment_template is not None:
                value = assignment_template.convert(value)
            data[key] = value
