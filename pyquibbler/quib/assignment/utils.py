from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List

import numpy as np

from pyquibbler.env import DEBUG

if TYPE_CHECKING:
    from pyquibbler.quib.assignment import PathComponent


def get_sub_data_from_object_in_path(obj: Any, path: List['PathComponent']):
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
                logging.warning(f"Attempted out of range assignment:"
                     f"\n\tdata: {data}"
                     f"\n\tpath: {path}"
                     f"\n\tfailed path component: {component.component}"
                     f"\n\texception: {e}")

        last_element = new_element
    return last_element
