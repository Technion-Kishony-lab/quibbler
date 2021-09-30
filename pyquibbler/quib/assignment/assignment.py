from dataclasses import dataclass
from typing import Any, Optional

from .assignment_template import AssignmentTemplate


@dataclass
class Assignment:
    """
    Represents a change performed on a quib.
    """
    key: Any
    value: Any

    def __repr__(self):
        return f'[{self.key}] = {self.value}'

    def apply(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        value = self.value if assignment_template is None else assignment_template.convert(self.value)
        data[self.key] = value
