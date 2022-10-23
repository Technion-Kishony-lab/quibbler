import numpy as np
from dataclasses import dataclass

from typing import Any, Type, Optional, Callable
from .general_utils import is_object_array, is_non_object_array, Kwargs, Args

from .numpy_original_functions import np_full

from pyquibbler.env import DEBUG
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.path import Path, PathComponent, Paths


SHALLOW_MAX_DEPTH = 2
SHALLOW_MAX_LENGTH = 100


@dataclass
class CannotCastObjectByOtherObjectException(PyQuibblerException):

    def __str__(self):
        return "New object cannot be casted by previous object."


def recursively_replace_objects_in_object(func: Callable, obj: Any):
    """
    Recursively replace each sub_object in obj with func(sub_object)
    """
    new_obj = func(obj)
    if new_obj is not obj:
        return new_obj
    if isinstance(obj, (tuple, list, set)):
        return type(obj)(recursively_replace_objects_in_object(func, sub_obj) for sub_obj in obj)
    if isinstance(obj, dict):
        return {key: recursively_replace_objects_in_object(func, sub_obj) for key, sub_obj in obj.items()}
    if is_object_array(obj, np.ndarray):
        return np.array((recursively_replace_objects_in_object(func, sub_obj) for sub_obj in obj), dtype=object)


def iter_objects_matching_criteria_in_object_recursively(func: Callable, obj: Any,
                                                         max_depth: Optional[int] = None,
                                                         max_length: Optional[int] = None,
                                                         prevent_repetitions: bool = True):
    """
    Returns an iterator for objects matching a criteria defined by func (func should return True/False).
    If prevent_repetitions=True, objects that appear more than once will not be repeated.
    When `max_depth` is given, limits the depth in which quibs are looked for.
    `max_depth=0` means only `obj` itself will be checked and replaced,
    `max_depth=1` means `obj` and all objects it directly references, and so on.
    When `max_length` is given, does not recurse into iterables larger than `max_length`.
    """
    objects = set()
    if func(obj):
        if prevent_repetitions:
            if obj not in objects:
                objects.add(obj)
                yield obj
        else:
            yield obj

    elif max_depth is None or max_depth > 0:
        # Recurse into composite objects
        if isinstance(obj, slice):
            obj = (obj.start, obj.stop, obj.step)
        if is_object_array(obj):
            obj = tuple(obj.ravel())
        if isinstance(obj, (tuple, list, set)):
            # This is a fixed-size collection
            if max_length is None or len(obj) <= max_length:
                # The collection is small enough
                next_max_depth = None if max_depth is None else max_depth - 1
                for sub_obj in obj:
                    yield from iter_objects_matching_criteria_in_object_recursively(func, sub_obj,
                                                                                    next_max_depth, max_length,
                                                                                    prevent_repetitions)


def iter_objects_of_type_in_object_recursively(object_type: Type, obj,
                                               max_depth: Optional[int] = None,
                                               max_length: Optional[int] = None):
    def is_type(sub_obj):
        return isinstance(sub_obj, object_type)

    yield from iter_objects_matching_criteria_in_object_recursively(is_type, obj, max_depth, max_length)


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


def iter_objects_of_type_in_object_shallowly(object_type: Type, obj: Any):
    """
    Returns an iterator for quib objects nested within the given python object,
    with limited width and length while scanning for quibs.
    """
    return iter_objects_of_type_in_object_recursively(object_type, obj, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH)


def iter_objects_of_type_in_object(object_type: Type, obj: Any, recursive: bool = False):
    if recursive:
        return iter_objects_of_type_in_object_recursively(object_type, obj)
    result = iter_objects_of_type_in_object_shallowly(object_type, obj)
    if DEBUG:
        from pyquibbler.quib.exceptions import NestedQuibException
        collected_result = set(result)
        result = iter(collected_result)
        expected = set(iter_objects_of_type_in_object_recursively(object_type, obj))
        if collected_result != expected:
            raise NestedQuibException(obj, expected - collected_result)
    return result


def iter_object_type_in_args_kwargs(object_type, args: Args, kwargs: Kwargs):
    """
    Returns an iterator for all objects of a type nested in the given args and kwargs.
    """
    return iter_objects_of_type_in_object(object_type, (*args, *kwargs.values()))


ITERATE_ON_OBJECT_ARRAYS = False


def recursively_run_func_on_object(func: Callable, obj: Any,
                                   path: Optional[Path] = None, max_depth: Optional[int] = None,
                                   max_length: Optional[int] = None,
                                   with_path: bool = False,
                                   ):
    if with_path:
        path = path or []
    if max_depth is None or max_depth > 0:
        # Recurse into composite objects
        next_max_depth = None if max_depth is None else max_depth - 1

        if isinstance(obj, (tuple, list, set)) and (max_length is None or len(obj) <= max_length):
            return type(obj)((recursively_run_func_on_object(
                func, sub_obj,
                [*path, PathComponent(i)] if with_path else None,
                next_max_depth,
                with_path=with_path)
                for i, sub_obj in enumerate(obj)))
        elif isinstance(obj, dict) and (max_length is None or len(obj) <= max_length):
            return type(obj)({key: recursively_run_func_on_object(
                func, sub_obj,
                [*path, PathComponent(key)] if with_path else None,
                next_max_depth,
                with_path=with_path)
                for key, sub_obj in obj.items()})
        elif isinstance(obj, slice):
            return slice(
                recursively_run_func_on_object(
                    func, obj.start,
                    [*path, PathComponent("start")] if with_path else None,
                    next_max_depth,
                    with_path=with_path),
                recursively_run_func_on_object(
                    func, obj.stop,
                    [*path, PathComponent("stop")] if with_path else None,
                    next_max_depth,
                    with_path=with_path),
                recursively_run_func_on_object(
                    func, obj.step,
                    [*path, PathComponent("step")] if with_path else None,
                    next_max_depth,
                    with_path=with_path), )
        elif ITERATE_ON_OBJECT_ARRAYS and is_object_array(obj):
            new_array = np_full(obj.shape, None, dtype=object)
            for indices, value in np.ndenumerate(obj):
                new_array[indices] = \
                    recursively_run_func_on_object(
                        func, obj[indices],
                        [*path, PathComponent(indices)] if with_path else None,
                        next_max_depth,
                        with_path=with_path)
            return new_array

    return func(path, obj) if with_path else func(obj)


def get_paths_for_objects_of_type(obj: Any, type_: Type) -> Paths:
    """
    Get paths for all objects of a certain `type_` within an `obj`
    """
    paths = []

    def add_path_if_isinstance(path, inner_obj):
        if isinstance(inner_obj, type_):
            paths.append(path)

    recursively_run_func_on_object(func=add_path_if_isinstance, obj=obj, with_path=True)
    return paths


def recursively_compare_objects(obj1: Any, obj2: Any, type_only=False) -> bool:
    # recursively compare object types (type_only=True), or type and value (type_only=False)

    if type(obj1) is not type(obj2):
        return False

    if isinstance(obj1, (float, int, str)):
        return type_only or obj1 == obj2

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
        return obj1.dtype is obj2.dtype and (type_only or np.array_equal(obj1, obj2))

    return obj1 == obj2


def recursively_cast_one_object_by_other(template: Any, obj: Any) -> Any:
    # Recursively cast one object based on the type of another

    if isinstance(template, (float, int, str)):
        return type(template)(obj)

    if is_object_array(template):
        obj = np.array(obj, dtype=object)
        if template.shape != obj.shape:
            raise CannotCastObjectByOtherObjectException()
        return np.vectorize(recursively_cast_one_object_by_other, otypes=[object])(template, obj)

    if is_non_object_array(template):
        return np.array(obj, dtype=template.dtype)

    if type(obj) is not type(template):
        raise CannotCastObjectByOtherObjectException()

    if isinstance(template, (tuple, list, set)):
        if len(template) != len(obj):
            raise CannotCastObjectByOtherObjectException()
        return type(template)(recursively_cast_one_object_by_other(sub_template, sub_obj)
                              for sub_template, sub_obj in zip(template, obj))

    if isinstance(template, dict):
        if len(template) != len(obj):
            raise CannotCastObjectByOtherObjectException()
        return {recursively_cast_one_object_by_other(sub_template_key, sub_obj_key):
                recursively_cast_one_object_by_other(sub_template_val, sub_obj_val)
                for sub_template_key, sub_obj_key, sub_template_val, sub_obj_val
                in zip(template.keys(), obj.keys(), template.values(), obj.values())}

    raise CannotCastObjectByOtherObjectException()
