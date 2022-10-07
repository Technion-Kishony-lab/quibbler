import copy
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Iterable
from numpy.typing import NDArray

import numpy as np

from pyquibbler.exceptions import PyQuibblerException

from .path_component import Path, SpecialComponent


def de_array_by_template(array: NDArray, obj: Any) -> Any:
    """
    This reverses the operation array = np.array(obj). It creates a new object that follows the template of `obj`,
    with the elements of `array`.
    """

    if isinstance(obj, (list, tuple)):
        return type(obj)(de_array_by_template(sub_array, sub_obj)
                         for sub_array, sub_obj in zip(array, obj))

    return array


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

        if cls == slice:
            obj = getattr(obj, cmp)
        elif cmp is True:
            pass
        elif cmp is SpecialComponent.ALL:
            pass
        elif isinstance(cmp, tuple) and len(cmp) == 1 and isinstance(obj, (list, tuple)):
            obj = obj[cmp[0]]
        elif component.is_nd_reference() and isinstance(obj, (list, tuple)):
            obj = np.array(obj, dtype=object)[cmp]
        else:
            obj = obj[cmp]

        if component.extract_element_out_of_array:
            assert isinstance(obj, np.ndarray) and obj.size == 1
            obj = obj.reshape(tuple())[tuple()]  # get element out of a size-1 array with any number of dimensions

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
    if not obj.flags.writeable:
        # To resolve failed test: test_quib_representing_read_only_array
        obj = obj.copy()
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
    tuple: set_for_tuple,
    dict: set_for_dict,
    np.ndarray: set_for_ndarray,
    slice: set_for_slice,
}


def deep_set(data: Any, path: Path,
             value: Any,
             raise_on_failure: bool = False,
             should_copy_objects_referenced: bool = True):
    """
    Go path by path setting value, each time ensuring we don't lost copied values (for example if there was
    fancy indexing) by making sure to set recursively back anything that made an assignment.
    We don't do this recursively for performance reasons
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
        is_non_array_indexed_by_array_style_indexing = isinstance(new_element, (list, tuple)) \
            and (component.is_nd_reference()
                 or cmp is Ellipsis
                 or isinstance(cmp, slice) and not isinstance(last_element, Iterable))
        if is_non_array_indexed_by_array_style_indexing:
            # To access an array-like object (list or tuple, potentially nested), with array-style indexing
            # we convert to nd.array and then back
            original_new_element = new_element
            new_element = np.array(new_element, dtype=object)
        elif isinstance(new_element, np.ndarray) and hasattr(new_element, 'base') \
                and should_copy_objects_referenced:
            # new_element is a view. we need to make a copy.
            new_element = np.array(new_element)

        setter = SETTERS.get(type(new_element), set_key_to_value)
        try:
            new_element = setter(new_element, cmp, last_element)
        except IndexError as e:
            if raise_on_failure:
                raise FailedToDeepAssignException(path=path, exception=e)
        if is_non_array_indexed_by_array_style_indexing:
            new_element = de_array_by_template(new_element, original_new_element)

        last_element = new_element
    return last_element
