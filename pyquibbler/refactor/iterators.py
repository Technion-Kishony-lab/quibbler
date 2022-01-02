import functools
import itertools
from inspect import signature
from typing import Tuple, Any, Mapping, Type, Optional, Callable

from pyquibbler.env import DEBUG
from pyquibbler.quib.utils import NestedQuibException, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH, QuibRef


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
    if isinstance(obj, QuibRef):
        obj = obj.quib
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
    bound_args = signature(func).bind(*args, **kwargs)
    if apply_defaults:
        bound_args.apply_defaults()
    return bound_args.arguments.items()