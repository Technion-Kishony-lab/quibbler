import numpy as np
from warnings import warn
from dataclasses import dataclass
from typing import Any, List, Optional, Union, Dict, Hashable

from .assignment import Assignment, PathComponent, get_hashable_path
from .assignment_template import AssignmentTemplate
from ..utils import deep_copy_without_quibs_or_artists, recursively_run_func_on_object
from ...env import DEBUG


@dataclass
class AssignmentRemoval:
    path: List[PathComponent]


def get_sub_data_from_object_in_path(obj: Any, path: List[PathComponent]):
    """
    Get the data from an object in a given path.
    """
    for component in path:
        obj = obj[component.component]
    return obj


def deep_assign_data_with_paths(data: Any, path: List[PathComponent], value: Any):
    """
    Go path by path setting value, each time ensuring we don't lost copied values (for example if there was
    fancy indexing) by making sure to set recursively back anything that made an assignment/
    We don't do this recursively for performance reasons- there could potentially be a very long string of
    assignments given to the user's whims
    """
    if len(path) == 0:
        return value

    *pre_components, last_component = path

    elements = [data]
    for component in pre_components:
        last_element = elements[-1][component.component]
        elements.append(last_element)

    last_element = value
    for i, component in enumerate(reversed(path)):
        new_element = elements[-(i + 1)]

        if isinstance(component.component, tuple) and not isinstance(new_element, np.ndarray):
            # We can't access a regular list with a tuple, so we're forced to convert to a numpy array
            new_element = np.array(new_element)

        try:
            new_element[component.component] = last_element
        except IndexError as e:
            if DEBUG:
                warn(f"Attempted out of range assignment:"
                     f"\n\tdata: {data}"
                     f"\n\tpath: {path}"
                     f"\n\tfailed path component: {component.component}"
                     f"\n\texception: {e}")

        last_element = new_element
    return last_element


class Overrider:
    """
    Gathers overriding assignments performed on a quib in order to apply them on a quib value.
    """

    def __init__(self):
        self._paths_to_assignments: Dict[Hashable, Union[Assignment, AssignmentRemoval]] = {}

    def _add_to_paths_to_assignments(self, assignment: Union[Assignment, AssignmentRemoval]):
        hashable_path = get_hashable_path(assignment.path)
        # We need to first remove and then add to make sure the new key value pair are now first in the dict
        if hashable_path in self._paths_to_assignments:
            self._paths_to_assignments.pop(hashable_path)
        self._paths_to_assignments[hashable_path] = assignment

    def add_assignment(self, assignment: Assignment):
        """
        Adds an override to the overrider - data[key] = value.
        """
        self._add_to_paths_to_assignments(assignment)

    def remove_assignment(self, path: List[PathComponent]):
        """
        Remove overriding in a specific path.
        """
        if self._paths_to_assignments:
            self._add_to_paths_to_assignments(AssignmentRemoval(path))

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Deep copies the argument and returns said data with applied overrides
        """
        from pyquibbler import timer
        original_data = data
        with timer("quib_overriding"):
            data = deep_copy_without_quibs_or_artists(data)
            for assignment in self._paths_to_assignments.values():
                if isinstance(assignment, AssignmentRemoval):
                    value = get_sub_data_from_object_in_path(original_data, assignment.path)
                    path = assignment.path
                else:
                    value = assignment.value if assignment_template is None \
                        else assignment_template.convert(assignment.value)
                    path = assignment.path
                data = deep_assign_data_with_paths(data, path, value)

        return data

    def fill_override_mask(self, false_mask):
        """
        Given a mask in the desired shape with all values set to False, update it so
        all cells in overridden indexes will be set to True.
        """
        mask = false_mask
        for assignment in self:
            if isinstance(assignment, AssignmentRemoval):
                path = assignment.path
                val = False
            else:
                path = assignment.path
                val = True
            if isinstance(path[-1].component, slice):
                inner_data = get_sub_data_from_object_in_path(mask, path[:-1])
                if not isinstance(inner_data, np.ndarray):
                    val = recursively_run_func_on_object(lambda x: val, inner_data)
            mask = deep_assign_data_with_paths(mask, path, val)
        return mask

    def __getitem__(self, item) -> Assignment:
        return list(self._paths_to_assignments.values())[item]

    def __repr__(self):
        return repr(self._paths_to_assignments.values())
