from dataclasses import dataclass
from typing import Any, Optional, TYPE_CHECKING, List, Union, Tuple, Type

if TYPE_CHECKING:
    from ..quib import Quib


ReplaceObject = object()

AssignmentPath = Union[str, Tuple, Any]


@dataclass
class Assignment:
    """
    A change performed on a quib.
    """
    value: Any

    paths: List[AssignmentPath]


@dataclass
class QuibWithAssignment:
    """
    A quib together with it's assignment
    """
    quib: 'Quib'
    assignment: Assignment

    def apply(self):
        self.quib.assign(self.assignment)
