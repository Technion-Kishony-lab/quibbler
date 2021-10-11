from typing import Any, List, Optional, Iterable

import numpy as np

from .assignment import Assignment, PathComponent, PathComponent
from .assignment_template import AssignmentTemplate
from ..utils import deep_copy_without_quibs_or_artists


def deep_assign_data_with_paths(data: Any, path: List[PathComponent], value: Any):
    """
    Go path by path setting value, each time ensuring we don't lost copied values (for example if there was
    fancy indexing) by making sure to set recursively back anything that made an assignment/
    We don't do this recursively for performance reasons- there could potentially be a very long string of
    assignments given to the user's whims
    """
    *pre_components, last_component = path

    elements = [data]
    for component in pre_components:
        last_element = elements[-1][component]
        elements.append(last_element)

    last_element = value
    for i, component in enumerate(reversed(path)):
        new_element = elements[-(i + 1)]
        if component is ...:
            # We manually do this even though numpy would have supported this (ie x[...] = v would
            # have set all values to x, even in a zero dimension array (which any type in numpy represents)),
            # but since we might not be with a numpy type we need to do it ourselves- we simply switch last_element
            # to be the new element and by this we set the whole thing
            new_element = last_element
        else:
            if isinstance(component, tuple) and not isinstance(new_element, np.ndarray):
                # We can't access a regular list with a tuple, so we're forced to convert to a numpy array
                new_element = np.array(new_element)
            new_element[component] = last_element
        last_element = new_element
    return last_element


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
        from pyquibbler import timer
        with timer("quib_overriding"):
            data = deep_copy_without_quibs_or_artists(data)
            for assignment in self._assignments:
                value = assignment.value if assignment_template is None else assignment_template.convert(assignment.value)
                data = deep_assign_data_with_paths(data, assignment.path, value)

        return data

    def __getitem__(self, item) -> Assignment:
        return self._assignments[item]

    def __repr__(self):
        return repr(self._assignments)
