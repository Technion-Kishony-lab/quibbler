import functools
import itertools
import numpy as np
from typing import Tuple, Any, Mapping, Type, Optional, Callable

from pyquibbler.env import DEBUG
from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.path import Path, PathComponent
from pyquibbler.utils import get_signature_for_func
from dataclasses import dataclass
SHALLOW_MAX_DEPTH = 2
SHALLOW_MAX_LENGTH = 100


@dataclass
class CannotCastObjectByOtherObjectException(PyQuibblerException):

    def __str__(self):
        return "New object cannot be casted by previous object."


def iter_objects_of_type_in_object_recursively(object_type: Type,
                                               obj, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    """
    Returns an iterator for objects of a type nested in the given python object.
    Objects that appear more than once will not be repeated.
    When `max_depth` is given, limits the depth in which quibs are looked for.
    `max_depth=0` means only `obj` itself will be checked and replaced,
    `max_depth=1` means `obj` and all objects it directly references, and so on.
    When `max_length` is given, does not recurse into iterables larger than `max_length`.
    """
    objects = set()
    if isinstance(obj, object_type):
        if obj not in objects:
            objects.add(obj)
            yield obj
    elif max_depth is None or max_depth > 0:
        # Recurse into composite objects
        if isinstance(obj, slice):
            obj = (obj.start, obj.stop, obj.step)
        if isinstance(obj, (tuple, list, set)):
            # This is a fixed-size collection
            if max_length is None or len(obj) <= max_length:
                # The collection is small enough
                next_max_depth = None if max_depth is None else max_depth - 1
                for sub_obj in obj:
                    yield from iter_objects_of_type_in_object_recursively(object_type,
                                                                          sub_obj, next_max_depth, max_length)


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


def iter_objects_of_type_in_object(object_type: Type, obj: Any, force_recursive: bool = False):
    if force_recursive:
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


def iter_object_type_in_args(object_type, args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Returns an iterator for all objects of a type nested in the given args and kwargs.
    """
    return itertools.chain(*map(functools.partial(iter_objects_of_type_in_object, object_type),
                                itertools.chain(args, kwargs.values())))


def iter_args_and_names_in_function_call(func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any],
                                         apply_defaults: bool):
    """
    Given a specific function call - func, args, kwargs - return an iterator to (name, val) tuples
    of all arguments that would have been passed to the function.
    If apply_defaults is True, add the default values from the function to the iterator.
    """
    sig = get_signature_for_func(func)
    bound_args = sig.bind(*args, **kwargs)
    if apply_defaults:
        bound_args.apply_defaults()
    return bound_args.arguments.items()


def recursively_run_func_on_object(func: Callable, obj: Any,
                                   path: Optional[Path] = None, max_depth: Optional[int] = None,
                                   max_length: Optional[int] = None,
                                   with_path: bool = False,
                                   ):
    path = path or []
    if max_depth is None or max_depth > 0:
        # Recurse into composite objects
        next_max_depth = None if max_depth is None else max_depth - 1

        if isinstance(obj, (tuple, list, set)) and (max_length is None or len(obj) <= max_length):
            return type(obj)((recursively_run_func_on_object(func, sub_obj,
                                                             [*path, PathComponent(component=i,
                                                                                   indexed_cls=type(obj))],
                                                             next_max_depth,
                                                             with_path=with_path)
                              for i, sub_obj in enumerate(obj)))
        elif isinstance(obj, dict) and (max_length is None or len(obj) <= max_length):
            return type(obj)({key: recursively_run_func_on_object(func, sub_obj,
                                                                  [*path, PathComponent(component=key,
                                                                                        indexed_cls=type(obj))],
                                                                  next_max_depth,
                                                                  with_path=with_path)
                              for key, sub_obj in obj.items()})
        elif isinstance(obj, slice):
            return slice(recursively_run_func_on_object(func, obj.start,
                                                        [*path, PathComponent(
                                                            component="start",
                                                            indexed_cls=slice
                                                        )],
                                                        next_max_depth,
                                                        with_path=with_path),
                         recursively_run_func_on_object(func, obj.stop,
                                                        [*path, PathComponent(
                                                            component="stop",
                                                            indexed_cls=slice
                                                        )],
                                                        next_max_depth,
                                                        with_path=with_path),
                         recursively_run_func_on_object(func, obj.step,
                                                        [*path, PathComponent(
                                                            component="step",
                                                            indexed_cls=slice
                                                        )],
                                                        next_max_depth,
                                                        with_path=with_path), )
    return func(path, obj) if with_path else func(obj)


def get_paths_for_objects_of_type(obj: Any, type_: Type):
    """
    Get paths for all objects of a certain `type_` within an `obj`
    """
    paths = []

    def add_path_if_isinstance(path, inner_obj):
        if isinstance(inner_obj, type_):
            paths.append(path)

    recursively_run_func_on_object(func=add_path_if_isinstance, obj=obj, with_path=True)
    return paths


def recursively_compare_objects_type(obj1: Any, obj2: Any, type_only=True) -> bool:
    # recursively compare object types (type_only=True), or type and value (type_only=False)

    if type(obj1) is not type(obj2):
        return False

    if isinstance(obj1, (float, int, str)):
        return type_only or obj1 == obj2

    if isinstance(obj1, (tuple, list, set)):
        if len(obj1) != len(obj2):
            return False
        return all(recursively_compare_objects_type(sub_obj1, sub_obj2, type_only)
                   for sub_obj1, sub_obj2 in zip(obj1, obj2))

    if isinstance(obj1, dict):
        if len(obj1) != len(obj2):
            return False
        return all(recursively_compare_objects_type(key1, key2, type_only)
                   for key1, key2 in zip(obj1.keys(), obj2.keys())) \
            and all(recursively_compare_objects_type(val1, val2, type_only)
                    for val1, val2 in zip(obj1.values(), obj2.values()))

    if isinstance(obj1, np.ndarray) and obj1.dtype is object:
        if obj1.shape != obj2.shape:
            return False

        return np.all(np.vectorize(recursively_compare_objects_type)(obj1, obj2, type_only))

    if isinstance(obj1, np.ndarray) and obj1.dtype is not object:
        return obj1.dtype is obj2.dtype and (type_only or np.array_equal(obj1, obj2))

    return False


def recursively_cast_one_object_by_other(template: Any, obj: Any) -> Any:
    # Recursively cast one object based on the type of another

    if isinstance(template, (float, int, str)):
        return type(template)(obj)

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

    if isinstance(template, np.ndarray) and template.dtype is object:
        if template.shape != obj.shape:
            raise CannotCastObjectByOtherObjectException()
        return np.vectorize(recursively_cast_one_object_by_other, otypes=[object])(template, obj)

    if isinstance(template, np.ndarray) and template.dtype is not object:
        return np.array(obj, dtype=template.dtype)

    raise CannotCastObjectByOtherObjectException()
