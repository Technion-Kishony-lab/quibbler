from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, List, Type

import numpy as np

if TYPE_CHECKING:
    from ..quib import Quib


def get_nd_working_component_value_from_path(path: List[PathComponent], raise_on_empty_path: bool = False):
    """
    Get the first working component value you can from the path- this will always be entirely "squashed", so you will
    get a component that expresses everything possible before needing to go another step "deeper" in

    If no component is found (path is empty), the path expresses getting "everything"- so we give a true value
    """
    return path[0].component if len(path) > 0 else True


@dataclass
class PathComponent:
    indexed_cls: Type
    component: Any

    def references_field_in_field_array(self):
        """
        Whether or not the component references a field in a field array
        It's important to note that this method is necessary as we need to dynamically decide whether a __setitem__
        assignment is a field assignment or not. This is in contrast to setattr for example where we could have had a
        special PathComponent for it, as the interface for setting an attribute is different.
        """
        return (
                issubclass(self.indexed_cls, np.ndarray) and
                (
                        isinstance(self.component, str) or
                        (isinstance(self.component, list) and isinstance(self.component[0], str))
                )
        )


@dataclass
class Assignment:
    """
    A change performed on a quib.
    """
    value: Any
    path: List[PathComponent] = field(default_factory=list)

    def __eq__(self, other):
        if not isinstance(other, Assignment):
            return NotImplemented
        # array_equal works for all objects, and our value and paths might contain ndarrays
        return np.array_equal((self.value, self.path), (other.value, other.path))


@dataclass(frozen=True)
class QuibWithAssignment:
    """
    An assignment to be performed on a specific quib.
    """
    quib: Quib
    assignment: Assignment

    def apply(self) -> None:
        self.quib.assign(self.assignment)

    def override(self):
        self.quib.override(self.assignment, allow_overriding_from_now_on=False)


@dataclass(frozen=True)
class FrozenSlice:
    start: int
    step: int
    stop: int


def _hash_component_value(inner_component):
    if isinstance(inner_component, list):
        return tuple([_hash_component_value(x) for x in inner_component])
    elif isinstance(inner_component, np.ndarray):
        return inner_component.tobytes()
    elif isinstance(inner_component, slice):
        return FrozenSlice(inner_component.start, inner_component.step, inner_component.stop)
    elif isinstance(inner_component, tuple):
        return tuple([_hash_component_value(x) for x in inner_component])
    return inner_component


def get_hashable_path(path: List[PathComponent]):
    """
    Get a hashable path (list of pathcomponents)- this supports known indexing methods
    """
    return tuple([
        _hash_component_value(p.component) for p in path
    ])
