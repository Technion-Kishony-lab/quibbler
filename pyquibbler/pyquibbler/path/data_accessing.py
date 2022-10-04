import copy
from dataclasses import dataclass
from typing import Any, Dict, Tuple
from numpy.typing import NDArray

import numpy as np

from pyquibbler.env import DEBUG
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.debug_utils.logger import logger

from .path_component import Path, SpecialComponent


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
        cmp = component.component
        cls = type(obj)
        is_component_nd = component.is_nd_reference()

        if cls == slice:
            obj = getattr(obj, cmp)
        elif is_component_nd and cmp is True:
            pass
        elif is_component_nd and cmp is SpecialComponent.ALL:
            pass
        elif is_component_nd and isinstance(obj, (list, tuple)):
            obj = np.array(obj, dtype=object)[cmp]
        elif isinstance(cmp, tuple) and len(cmp) == 1 and isinstance(obj, (list, tuple)):
            obj = obj[cmp[0]]
        else:
            obj = obj[cmp]
        if component.extract_element_out_of_array:
            assert obj.size == 1
            obj = obj.reshape(tuple())[tuple()]  # get element out of array (works for any number of dimensions)

    return obj


def set_for_slice(sl_, attribute, value):
    if attribute == "start":
        return slice(value, sl_.stop, sl_.step)
    elif attribute == "stop":
        return slice(sl_.start, value, sl_.step)
    else:
        return slice(sl_.start, sl_.stop, value)


def set_for_tuple(tpl: Tuple, index: int, value):
    lst = list(tpl)
    lst[index] = value
    return tuple(lst)


def set_for_ndarray(obj: NDArray, component, value):
    if component is SpecialComponent.ALL:
        component = True
    obj[component] = value
    return obj


def set_for_dict(obj: Dict, key, value):
    if key is SpecialComponent.ALL:
        for k in obj.keys():
            obj[k] = value
    else:
        obj[key] = value
    return obj


def set_key_to_value(obj, key, value):
    obj[key] = value
    return obj


SETTERS = {
    slice: set_for_slice,
    tuple: set_for_tuple,
    dict: set_for_dict,
    np.ndarray: set_for_ndarray,
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

        cmp = component.component
        need_to_convert_back_to_original_type = False
        if component.is_nd_reference() and isinstance(new_element, (list, tuple)):
            # We are trying to access a non-array object, like or tuple, with array-style indexing
            original_type = type(new_element)
            new_element = np.array(new_element, dtype=object)
            need_to_convert_back_to_original_type = True
        elif isinstance(new_element, np.ndarray) and hasattr(new_element, 'base') \
                and should_copy_objects_referenced:
            # new_element is a view. we need to make a copy.
            new_element = np.array(new_element)

        setter = SETTERS.get(type(new_element), set_key_to_value)
        try:
            new_element = setter(new_element, cmp, last_element)
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
                     f"\n\tfailed path component: {cmp}"
                     f"\n\texception: {e}")
                )

        last_element = new_element
    return last_element
