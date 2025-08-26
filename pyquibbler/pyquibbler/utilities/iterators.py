import copy

import numpy as np

from typing import Any, Type, Optional, Callable
from .general_utils import is_object_array, is_non_object_array, Kwargs, Args

from .numpy_original_functions import np_full

from pyquibbler.path import Path, PathComponent, Paths

DEFAULT_MAX_DEPTH_ON_OBJECT_ARRAYS = -1
DEFAULT_MAX_DEPTH_ATTRIBUTES = -1


def _larger_than(max_val: Optional[int], val: int = 0):
    """We treat None as infinite"""
    if max_val is None:
        return True
    if val is None:
        return False
    return val < max_val


def is_user_object(obj):
    return (obj.__class__.__module__ != "builtins"
            and hasattr(obj, "__dict__"))


def iter_paths_and_objects_matching_criteria_in_object_recursively(func: Callable, obj: Any,
                                                                   max_depth: Optional[int] = None,
                                                                   max_length: Optional[int] = None,
                                                                   max_depth_on_object_arrays: int = DEFAULT_MAX_DEPTH_ON_OBJECT_ARRAYS,
                                                                   max_depth_on_attributes: int = DEFAULT_MAX_DEPTH_ATTRIBUTES,
                                                                   stop_on: type = None,
                                                                   with_path: bool = True,
                                                                   _path: Optional[Path] = None,
                                                                   ):

    if with_path and _path is None:
        _path = []

    next_max_depth = None if max_depth is None else max_depth - 1
    next_max_depth_in_case_of_object_arrays = max_depth_on_object_arrays if _larger_than(next_max_depth, max_depth_on_object_arrays) else next_max_depth
    next_max_depth_in_case_of_attributes = max_depth_on_attributes if _larger_than(next_max_depth, max_depth_on_attributes) else next_max_depth

    def extend_path(component, is_attr: bool = False):
        return [*_path, PathComponent(component, is_attr=is_attr)] if _path is not None else None

    def _recurse(sub_obj, component, is_attr: bool = False, is_object_array: bool = False, is_user_object: bool = False):
        if is_object_array:
            actual_next_max_depth = next_max_depth_in_case_of_object_arrays
        elif is_user_object:
            actual_next_max_depth = next_max_depth_in_case_of_attributes
        else:
            actual_next_max_depth = next_max_depth

        yield from iter_paths_and_objects_matching_criteria_in_object_recursively(
            func, sub_obj, actual_next_max_depth, max_length, max_depth_on_object_arrays, max_depth_on_attributes, stop_on,
            with_path, extend_path(component, is_attr))

    if not _larger_than(max_depth, -1):
        return

    # Check if current object matches criteria
    args = (_path,) if with_path else ()
    if func(obj, *args):
        yield (obj, _path) if with_path else obj

    if stop_on is not None and isinstance(obj, stop_on):
        return

    # Recurse into composite objects
    if isinstance(obj, (tuple, list)) and _larger_than(max_length, len(obj)-1):
        for i, sub_obj in enumerate(obj):
            yield from _recurse(sub_obj, i)
    elif isinstance(obj, dict) and _larger_than(max_length, len(obj)-1):
        for key, sub_obj in obj.items():
            yield from _recurse(sub_obj, key)
    elif isinstance(obj, slice):
        for attr in ('start', 'stop', 'step'):
            yield from _recurse(getattr(obj, attr), attr, is_attr=True)
    elif  _larger_than(max_depth_on_object_arrays, -1) and is_object_array(obj) and _larger_than(max_length, obj.size-1):
        for indices, value in np.ndenumerate(obj):
            yield from _recurse(value, indices, is_object_array=True)
    elif _larger_than(max_depth_on_attributes, -1) and is_user_object(obj):
        for attr_name, attr_value in vars(obj).items():
            try:
                yield from _recurse(attr_value, attr_name, is_attr=True, is_user_object=True)
            except AttributeError:
                pass


def iter_objects_of_type_in_object_recursively(object_type: Type, obj: Any,
                                               max_depth: Optional[int] = None,
                                               max_length: Optional[int] = None,
                                               prevent_repetitions: bool = True,
                                               max_depth_on_object_arrays: int = DEFAULT_MAX_DEPTH_ON_OBJECT_ARRAYS,
                                               max_depth_on_attributes: int = DEFAULT_MAX_DEPTH_ATTRIBUTES
                                               ):
    collected = set()

    def is_match(sub_obj) -> bool:
        if not isinstance(sub_obj, object_type):
            return False
        if prevent_repetitions:
            if id(sub_obj) in collected:
                return False
            collected.add(id(sub_obj))
        return True

    yield from iter_paths_and_objects_matching_criteria_in_object_recursively(
        is_match, obj,
        max_depth=max_depth,
        max_length=max_length,
        max_depth_on_object_arrays=max_depth_on_object_arrays,
        max_depth_on_attributes=max_depth_on_attributes,
        stop_on=object_type,
        with_path=False,
    )


def get_paths_for_objects_of_type(
        object_type: Type, obj: Any,
        max_depth: Optional[int] = None,
        max_length: Optional[int] = None,
        max_depth_on_object_arrays: int = DEFAULT_MAX_DEPTH_ON_OBJECT_ARRAYS,
        max_depth_on_attributes: int = DEFAULT_MAX_DEPTH_ATTRIBUTES) -> Paths:
    """
    Get paths for all objects of a certain `type_` within an `obj`
    """
    def is_match(sub_obj, _path) -> bool:
        return isinstance(sub_obj, object_type)

    return [path for _, path in
        iter_paths_and_objects_matching_criteria_in_object_recursively(
            is_match, obj,
            max_depth=max_depth,
            max_length=max_length,
            max_depth_on_object_arrays=max_depth_on_object_arrays,
            max_depth_on_attributes=max_depth_on_attributes,
            stop_on=object_type,
            with_path=True)
        ]


def is_iterator_empty(iterator):
    """
    Check if a given iterator is empty by getting one item from it.
    Note that this item will be lost!
    """
    try:
        next(iterator)
        return False
    except StopIteration:
        return True


def recursively_run_func_on_object(func: Callable, obj: Any,
                                   max_depth: Optional[int] = None,
                                   max_length: Optional[int] = None,
                                   max_depth_on_object_arrays: int = DEFAULT_MAX_DEPTH_ON_OBJECT_ARRAYS,
                                   max_depth_on_attributes: int = DEFAULT_MAX_DEPTH_ATTRIBUTES,
                                   stop_on: type = None,
                                   ):

    if not (_larger_than(max_depth, 0) and (stop_on is None or not isinstance(obj, stop_on))):
        return obj

    next_max_depth = None if max_depth is None else max_depth - 1
    next_max_depth_in_case_of_object_arrays = max_depth_on_object_arrays if _larger_than(next_max_depth, max_depth_on_object_arrays) else next_max_depth
    next_max_depth_in_case_of_attributes = max_depth_on_attributes if _larger_than(next_max_depth, max_depth_on_attributes) else next_max_depth

    def _recurse(sub_obj, is_object_array: bool = False, is_attr: bool = False, is_user_object: bool = False):
        if is_object_array:
            actual_next_max_depth = next_max_depth_in_case_of_object_arrays
        elif is_user_object:
            actual_next_max_depth = next_max_depth_in_case_of_attributes
        else:
            actual_next_max_depth = next_max_depth

        return recursively_run_func_on_object(
            func, sub_obj, actual_next_max_depth, max_length, max_depth_on_object_arrays, max_depth_on_attributes, stop_on)

    # Recurse into composite objects
    if isinstance(obj, (tuple, list)) and _larger_than(max_length, len(obj)-1):
        return type(obj)((_recurse(sub_obj) for i, sub_obj in enumerate(obj)))
    elif isinstance(obj, dict) and _larger_than(max_length, len(obj)) and _larger_than(max_length, len(obj)-1):
        return type(obj)({key: _recurse(value) for key, value in obj.items()})
    elif isinstance(obj, slice):
        return slice(*(_recurse(getattr(obj, attr), is_attr=True) for attr in ('start', 'stop', 'step')))
    elif _larger_than(max_depth_on_object_arrays, -1) and is_object_array(obj) and _larger_than(max_length, obj.size-1):
        new_array = np_full(obj.shape, None, dtype=object)
        for indices, value in np.ndenumerate(obj):
            new_array[indices] = _recurse(value, is_object_array=True)
        return new_array
    elif _larger_than(max_depth_on_attributes, -1) and is_user_object(obj):
        new_obj = copy.copy(obj)
        for attr_name, attr_value in vars(obj).items():
            try:
                setattr(new_obj, attr_name, _recurse(attr_value, is_attr=True, is_user_object=True))
            except AttributeError:
                pass
        return new_obj

    return func(obj)


def recursively_compare_objects(obj1: Any, obj2: Any, type_only=False) -> bool:
    """
    recursively compare two objects

    only compare types (type_only=True)
    compare type and value (type_only=False)
    compare value only (type_only=None)
    """

    if type_only is not None and type(obj1) is not type(obj2):
        return False

    if isinstance(obj1, (float, int, str)):
        return type_only is True or obj1 == obj2

    if isinstance(obj1, (tuple, list, set)):
        if len(obj1) != len(obj2):
            return False
        return all(recursively_compare_objects(sub_obj1, sub_obj2, type_only)
                   for sub_obj1, sub_obj2 in zip(obj1, obj2))

    if isinstance(obj1, dict):
        if len(obj1) != len(obj2):
            return False
        return all(recursively_compare_objects(key1, key2, type_only)
                   for key1, key2 in zip(obj1.keys(), obj2.keys())) \
            and all(recursively_compare_objects(val1, val2, type_only)
                    for val1, val2 in zip(obj1.values(), obj2.values()))

    if is_object_array(obj1):
        if obj1.shape != obj2.shape:
            return False

        return np.all(np.vectorize(recursively_compare_objects)(obj1, obj2, type_only))

    if is_non_object_array(obj1):
        return obj1.dtype is obj2.dtype and (type_only is True or np.array_equal(obj1, obj2))

    return obj1 == obj2
