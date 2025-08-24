import copy

import numpy as np

from typing import Any, Type, Optional, Callable
from .general_utils import is_object_array, is_non_object_array, Kwargs, Args

from .numpy_original_functions import np_full

from pyquibbler.path import Path, PathComponent, Paths

RECURSE_MODE_TO_PARAMS = {
    'shallow': {'max_depth': 2, 'max_length': 100},
    'deep': {'max_depth': None, 'max_length': None},
}

DEFAULT_ITERATE_ON_OBJECT_ARRAYS = False
DEFAULT_ITERATE_ON_ATTRIBUTES = False


def _larger_than(max_val: Optional[int], val: int = 0):
    if max_val is None:
        return True
    return val < max_val


def iter_paths_and_objects_matching_criteria_in_object_recursively(func: Callable, obj: Any,
                                                                   max_depth: Optional[int] = None,
                                                                   max_length: Optional[int] = None,
                                                                   recurse_mode: str = None,
                                                                   iterate_on_object_arrays: bool = DEFAULT_ITERATE_ON_OBJECT_ARRAYS,
                                                                   iterate_on_attributes: bool = DEFAULT_ITERATE_ON_ATTRIBUTES,
                                                                   stop_on: type = None,
                                                                   with_path: bool = True,
                                                                   _path: Optional[Path] = None,
                                                                   ):

    if with_path and _path is None:
        _path = []

    if recurse_mode is not None:
        params = RECURSE_MODE_TO_PARAMS[recurse_mode]
        max_depth = params['max_depth']
        max_length = params['max_length']

    next_max_depth = None if max_depth is None else max_depth - 1

    def extend_path(component, is_attr: bool = False):
        return [*_path, PathComponent(component, is_attr=is_attr)] if _path is not None else None

    def _recurse(sub_obj, component, is_attr: bool = False):
        yield from iter_paths_and_objects_matching_criteria_in_object_recursively(
            func, sub_obj, next_max_depth, max_length, None, iterate_on_object_arrays, iterate_on_attributes, stop_on,
            with_path, extend_path(component, is_attr))

    # Check if current object matches criteria
    args = (_path,) if with_path else ()
    if func(obj, *args):
        yield (obj, _path) if with_path else obj

    if not _larger_than(max_depth) or (stop_on is not None and isinstance(obj, stop_on)):
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
    elif iterate_on_object_arrays and is_object_array(obj) and _larger_than(max_length, obj.size-1):
        for indices, value in np.ndenumerate(obj):
            yield from _recurse(value, indices)
    elif iterate_on_attributes and hasattr(obj, '__dict__'):
        for attr_name, attr_value in vars(obj).items():
            try:
                yield from _recurse(attr_value, attr_name, is_attr=True)
            except AttributeError:
                pass


def iter_objects_of_type_in_object_recursively(object_type: Type, obj: Any,
                                               max_depth: Optional[int] = None,
                                               max_length: Optional[int] = None,
                                               recurse_mode: str = None,
                                               prevent_repetitions: bool = True,
                                               iterate_on_object_arrays: bool = DEFAULT_ITERATE_ON_OBJECT_ARRAYS,
                                               iterate_on_attributes: bool = DEFAULT_ITERATE_ON_ATTRIBUTES
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
        recurse_mode=recurse_mode,
        iterate_on_object_arrays=iterate_on_object_arrays,
        iterate_on_attributes=iterate_on_attributes,
        stop_on=object_type,
        with_path=False,
    )


def get_paths_for_objects_of_type(
        object_type: Type, obj: Any,
        max_depth: Optional[int] = None,
        max_length: Optional[int] = None,
        recurse_mode: str = None,
        iterate_on_object_arrays: bool = DEFAULT_ITERATE_ON_OBJECT_ARRAYS,
        iterate_on_attributes: bool = DEFAULT_ITERATE_ON_ATTRIBUTES) -> Paths:
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
            recurse_mode=recurse_mode,
            iterate_on_object_arrays=iterate_on_object_arrays,
            iterate_on_attributes=iterate_on_attributes,
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
                                   recurse_mode: Optional[str] = 'deep',
                                   iterate_on_object_arrays: bool = DEFAULT_ITERATE_ON_OBJECT_ARRAYS,
                                   iterate_on_attributes: bool = DEFAULT_ITERATE_ON_ATTRIBUTES,
                                   stop_on: type = None,
                                   ):

    if recurse_mode is not None:
        params = RECURSE_MODE_TO_PARAMS[recurse_mode]
        max_depth = params['max_depth']
        max_length = params['max_length']

    next_max_depth = None if max_depth is None else max_depth - 1

    def _recurse(sub_obj):
        return recursively_run_func_on_object(
            func, sub_obj, next_max_depth, max_length, None, iterate_on_object_arrays, iterate_on_attributes, stop_on)

    if not (_larger_than(max_depth) and (stop_on is None or not isinstance(obj, stop_on))):
        return obj

    # Recurse into composite objects
    if isinstance(obj, (tuple, list)) and _larger_than(max_length, len(obj)-1):
        return type(obj)((_recurse(sub_obj) for i, sub_obj in enumerate(obj)))
    elif isinstance(obj, dict) and _larger_than(max_length, len(obj)) and _larger_than(max_length, len(obj)-1):
        return type(obj)({key: _recurse(value) for key, value in obj.items()})
    elif isinstance(obj, slice):
        return slice(*(_recurse(getattr(obj, attr)) for attr in ('start', 'stop', 'step')))
    elif iterate_on_object_arrays and is_object_array(obj) and _larger_than(max_length, obj.size-1):
        new_array = np_full(obj.shape, None, dtype=object)
        for indices, value in np.ndenumerate(obj):
            new_array[indices] = _recurse(value)
        return new_array
    elif iterate_on_attributes and hasattr(obj, '__dict__'):
        new_obj = copy.copy(obj)
        for attr_name, attr_value in vars(obj).items():
            try:
                setattr(new_obj, attr_name, _recurse(attr_value))
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
