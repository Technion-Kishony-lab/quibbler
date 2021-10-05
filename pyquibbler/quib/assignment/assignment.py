from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..quib import Quib


@dataclass
class Assignment:
    """
    A change performed on a quib.
    """
    value: Any

    field: Optional[Any] = None


# This is not a dataclass as we would like to have field be a default arg
class IndicesAssignment(Assignment):
    """
    A change performed on a quib in specific indices.
    """

    def __repr__(self):
        return f'[{self.indices}] = {self.value})'

    def __init__(self, value: Any, indices: Any, field: Optional[str] = None):
        self.value = value
        self.indices = indices
        self.field = field


@dataclass
class QuibWithAssignment:
    """
    A quib together with it's assignment
    """
    quib: 'Quib'
    assignment: Assignment

    def apply(self):
        self.quib.assign(self.assignment)
