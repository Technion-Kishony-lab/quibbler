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
