from dataclasses import dataclass
from typing import List, Any

import numpy as np

from pyquibbler.env import DEBUG
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.logger import logger
from pyquibbler.path import PathComponent


@dataclass
class FailedToDeepAssignException(PyQuibblerException):

    path: List[PathComponent]
    exception: IndexError

    def __str__(self):
        return f"The path {''.join([f'[{p.component}]' for p in self.path])} " \
               f"was invalid in the data, and therefore could not be assigned with- " \
               f"failed on {self.exception}"


def deep_get(obj: Any, path: List['PathComponent']):
    """
    Get the data from an object in a given path.
    """
    for component in path:
        obj = obj[component.component]
    return obj


def deep_assign_data_in_path(data: Any, path: List[PathComponent], value: Any, raise_on_failure: bool = False):
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

        if (isinstance(component.component, (tuple, np.ndarray)) and not isinstance(new_element, np.ndarray)) or \
                (isinstance(new_element, np.ndarray) and hasattr(new_element, 'base')):
            # We can't access a regular list with a tuple, so we're forced to convert to a numpy array
            new_element = np.array(new_element)

        try:
            new_element[component.component] = last_element
        except IndexError as e:
            if raise_on_failure:
                raise FailedToDeepAssignException(path=path, exception=e)

            if DEBUG:
                logger.warning(
                    (f"Attempted out of range assignment:"
                     f"\n\tdata: {data}"
                     f"\n\tpath: {path}"
                     f"\n\tfailed path component: {component.component}"
                     f"\n\texception: {e}")
                )
        last_element = new_element
    return last_element
