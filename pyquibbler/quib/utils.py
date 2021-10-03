from __future__ import annotations
import functools
import numpy as np
from dataclasses import dataclass
from inspect import signature
from itertools import chain
from typing import Any, Optional, Set, TYPE_CHECKING, Callable, Tuple, Dict, Type
from copy import copy

from pyquibbler.env import is_debug
from pyquibbler.exceptions import DebugException, PyQuibblerException

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

SHALLOW_MAX_DEPTH = 1
SHALLOW_MAX_LENGTH = 100


def iter_args_and_names_in_function_call(func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any],
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


@dataclass
class NestedQuibException(DebugException):
    obj: Any
    nested_quibs: Set[Quib]

    def __str__(self):
        return 'PyQuibbler does not support calling functions with arguments that contain nested quibs.\n' \
               f'The quibs {self.nested_quibs} are nested within {self.obj}.'

    @classmethod
    def create_from_object(cls, obj: Any):
        return cls(obj, set(iter_quibs_in_object_recursively(obj)))


@dataclass
class FunctionCalledWithNestedQuibException(PyQuibblerException):
    func: Callable
    nested_quibs_by_arg_names: Dict[str, Set[Quib]]

    def __str__(self):
        return f'The function {self.func} was called with nested Quib objects. This is not supported.\n' + \
               '\n'.join(f'The argument "{arg}" contains the quibs: {quibs}'
                         for arg, quibs in self.nested_quibs_by_arg_names)

    @classmethod
    def from_call(cls, func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any]):
        """
        Creates an instance of this exception given a specific function call,
        by finding the erroneously nested quibs.
        """
        nested_quibs_by_arg_names = {}
        for name, val in iter_args_and_names_in_function_call(func, args, kwargs, False):
            quibs = set(iter_quibs_in_object_recursively(val))
            if quibs:
                nested_quibs_by_arg_names[name] = quibs
        assert nested_quibs_by_arg_names
        return cls(func, nested_quibs_by_arg_names)


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
                                   max_depth: Optional[int] = None, max_length: Optional[int] = None):
    if max_depth is None or max_depth > 0:
        # Recurse into composite objects
        next_max_depth = None if max_depth is None else max_depth - 1
        if isinstance(obj, (tuple, list, set)):
            if max_length is None or len(obj) <= max_length:
                return type(obj)(recursively_run_func_on_object(func, sub_obj, next_max_depth) for sub_obj in obj)
        elif isinstance(obj, slice):
            return slice(recursively_run_func_on_object(func, obj.start, next_max_depth),
                         recursively_run_func_on_object(func, obj.stop, next_max_depth),
                         recursively_run_func_on_object(func, obj.step, next_max_depth))
    return func(obj)


def deep_copy_without_quibs_or_artists(obj: Any, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    from pyquibbler.quib import Quib
    from matplotlib.artist import Artist

    def copy_if_not_quib_or_artist(o):
        if isinstance(o, (Quib, Artist)):
            return o
        return copy(o)

    return recursively_run_func_on_object(func=copy_if_not_quib_or_artist, max_length=max_length,
                                          max_depth=max_depth, obj=obj)


def deep_copy_and_replace_quibs_with_vals(obj: Any, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    """
    Deep copy an object while replacing quibs with their values.
    When `max_depth` is given, limits the depth in which quibs are looked for.
    `max_depth=0` means only `obj` itself will be checked and replaced,
    `max_depth=1` means `obj` and all objects it directly references, and so on.
    When `max_length` is given, does not recurse into iterables larger than `max_length`.
    """
    from pyquibbler.quib import Quib
    from matplotlib.artist import Artist

    def replace_with_value_if_quib_or_copy(o):
        if isinstance(o, Quib):
            return o.get_value()
        if isinstance(o, Artist):
            return o
        return copy(o)

    return recursively_run_func_on_object(func=replace_with_value_if_quib_or_copy, max_depth=max_depth,
                                          max_length=max_length, obj=obj)


def shallow_copy_and_replace_quibs_with_vals(obj: Any):
    """
    Deep copy `obj` while replacing quibs with their values, with a limited depth and length.
    """
    return deep_copy_and_replace_quibs_with_vals(obj, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH)


def copy_and_replace_quibs_with_vals(obj: Any):
    result = shallow_copy_and_replace_quibs_with_vals(obj)
    if is_debug():
        expected = deep_copy_and_replace_quibs_with_vals(obj)
        equal = np.array_equal(expected, result) if isinstance(expected, np.ndarray) else expected == result
        if not equal:
            raise NestedQuibException.create_from_object(obj)
    return result


def iter_quibs_in_object_recursively(obj, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    """
    Returns an iterator for quibs of a type nested in the given python object.
    Quibs that appear more than once will not be repeated.
    When `max_depth` is given, limits the depth in which quibs are looked for.
    `max_depth=0` means only `obj` itself will be checked and replaced,
    `max_depth=1` means `obj` and all objects it directly references, and so on.
    When `max_length` is given, does not recurse into iterables larger than `max_length`.
    """
    from pyquibbler.quib import Quib
    return iter_objects_of_type_in_object_recursively(Quib, obj, max_depth, max_length)


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
        if isinstance(obj, (tuple, list, set)):
            # This is a fixed-size collection
            if max_length is None or len(obj) <= max_length:
                # The collection is small enough
                next_max_depth = None if max_depth is None else max_depth - 1
                for sub_obj in obj:
                    yield from iter_objects_of_type_in_object_recursively(object_type,
                                                                          sub_obj, next_max_depth, max_length)


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
    if is_debug():
        collected_result = set(result)
        result = iter(collected_result)
        expected = set(iter_objects_of_type_in_object_recursively(object_type, obj))
        if collected_result != expected:
            raise NestedQuibException(obj, set(expected))
    return result


def iter_quibs_in_object(obj, force_recursive: bool = False):
    from pyquibbler.quib import Quib
    return iter_objects_of_type_in_object(Quib, obj, force_recursive)


def iter_object_type_in_args(object_type, args, kwargs):
    """
    Returns an iterator for all objects of a type nested in the given args and kwargs.
    """
    return chain(*map(functools.partial(iter_objects_of_type_in_object, object_type), chain(args, kwargs.values())))


def iter_quibs_in_args(args, kwargs):
    """
    Returns an iterator for all quib objects nested in the given args and kwargs.
    """
    from pyquibbler.quib import Quib
    return iter_object_type_in_args(Quib, args, kwargs)


def call_func_with_quib_values(func, args, kwargs):
    """
    Calls a function with the specified args and kwargs while replacing quibs with their values.
    """
    new_args = [copy_and_replace_quibs_with_vals(arg) for arg in args]
    kwargs = {name: copy_and_replace_quibs_with_vals(val) for name, val in kwargs.items()}
    try:
        return func(*new_args, **kwargs)
    except TypeError as e:
        if len(e.args) == 1 and 'Quib' in e.args[0]:
            raise FunctionCalledWithNestedQuibException.from_call(func, args, kwargs) from e
        raise


def call_method_with_quib_values(func, self, args, kwargs):
    """
    Calls an instance method with the specified args and kwargs while replacing quibs with their values.
    """
    return call_func_with_quib_values(func, [self, *args], kwargs)


def is_there_a_quib_in_object(obj, force_recursive: bool = False):
    """
    Returns true if there is a quib object nested inside the given object and false otherwise.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj, force_recursive))


def is_there_a_quib_in_args(args, kwargs):
    """
    Returns true if there is a quib object nested inside the given args and kwargs and false otherwise.
    For use by function wrappers that need to determine if the underlying function was called with a quib.
    """
    return not is_iterator_empty(iter_quibs_in_args(args, kwargs))
