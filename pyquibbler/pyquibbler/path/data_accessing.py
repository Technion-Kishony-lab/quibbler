import copy
from dataclasses import dataclass
from typing import Any

import numpy as np

from pyquibbler.env import DEBUG
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.debug_utils.logger import logger
from .path_component import Path


@dataclass
class FailedToDeepAssignException(PyQuibblerException):

    path: Path
    exception: IndexError

    def __str__(self):
        return f"The path {''.join([f'[{p.component}]' for p in self.path])} " \
               f"was invalid in the data, and therefore could not be assigned with- " \
               f"failed on {self.exception}"


def deep_get(obj: Any, path: Path):
    """
    Get the data from an object in a given path.
    """
    for component in path:
        if isinstance(obj, np.ndarray) and component.indexed_cls is not None and component.indexed_cls != np.ndarray:
            # We allow specifying a path component that can reference multiple places in the array - for example,
            # if given a path
            # [PathComponent(np.ndarray, [True, True]), PathComponent(dict, "name"])]
            # This path would reference both names of the two dictionaries in the ndarray. This is very important when
            # it comes to invalidation, as it negates the necessity of needing two paths.
            # In deep get, this means we need to be able to get a field after an array - but there must necessarily be
            # only one value in the array, otherwise we wouldn't know which to return (e.g. in the above example-
            # which name?)
            flattened = np.array(obj.flat)
            assert len(flattened) == 1
            obj = flattened[0]

        if component.indexed_cls == slice:
            obj = getattr(obj, component.component)
        else:
            try:
                obj = obj[component.component]
            except TypeError:
                # We don't want to fail if it's a list that's being accessed as an nparray
                obj = np.array(obj)[component.component]
    return obj


def set_for_slice(sl_, attribute, value):
    if attribute == "start":
        return slice(value, sl_.stop, sl_.step)
    elif attribute == "stop":
        return slice(sl_.start, value, sl_.step)
    else:
        return slice(sl_.start, sl_.stop, value)


def set_for_tuple(tpl, index, value):
    lst = list(tpl)
    lst[index] = value
    return tuple(lst)


def set_key_to_value(obj, key, value):
    obj[key] = value
    return obj


SETTERS = {
    slice: set_for_slice,
    tuple: set_for_tuple
}


def deep_assign_data_in_path(data: Any, path: Path,
                             value: Any,
                             raise_on_failure: bool = False,
                             should_copy_objects_referenced: bool = True):
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
        if should_copy_objects_referenced:
            new_element = copy.copy(new_element)

        need_to_convert_back_to_original_type = False
        if isinstance(component.component, (tuple, np.ndarray)) and not isinstance(new_element, np.ndarray):
            # We can't access a regular list with a tuple, so we're forced to convert to a numpy array
            original_type = type(new_element)
            new_element = np.array(new_element, dtype=object)
            need_to_convert_back_to_original_type = True
        elif isinstance(new_element, np.ndarray) and hasattr(new_element, 'base'):
            new_element = np.array(new_element)

        try:
            setter = SETTERS.get(component.indexed_cls, set_key_to_value)
            new_element = setter(new_element, component.component, last_element)
            if need_to_convert_back_to_original_type:
                new_element = original_type(new_element.tolist())
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
