from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, List, Union, Tuple

if TYPE_CHECKING:
    from ..quib import Quib

AssignmentPath = Union[str, Tuple, type(Ellipsis)]


@dataclass
class Assignment:
    """
    A change performed on a quib.
    """
    value: Any
    paths: List[AssignmentPath] = field(default_factory=list)


@dataclass
class QuibWithAssignment:
    """
    A quib together with it's assignment
    """
    quib: Quib
    assignment: Assignment

    def apply(self):
        self.quib.assign(self.assignment)

    def override(self):
        self.quib.override(self.assignment, allow_overriding_from_now_on=False)

    def __hash__(self):
        return id(self)

    def __eq__(self, other):
        return self is other
