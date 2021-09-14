from __future__ import annotations
from dataclasses import dataclass
from itertools import chain
from typing import Any, Optional, Set, TYPE_CHECKING
from copy import copy

from pyquibbler.env import is_debug
from pyquibbler.exceptions import DebugException

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

SHALLOW_MAX_DEPTH = 1
SHALLOW_MAX_LENGTH = 100


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


def deep_copy_and_replace_quibs_with_vals(obj: Any, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    """
    Deep copy an object while replacing quibs with their values.
    When `max_depth` is given, limits the depth in which quibs are looked for.
    `max_depth=0` means only `obj` itself will be checked and replaced,
    `max_depth=1` means `obj` and all objects it directly references, and so on.
    When `max_length` is given, does not recurse into iterables larger than `max_length`.
    """
    from pyquibbler.quib import Quib
    if isinstance(obj, Quib):
        return obj.get_value()
    if max_depth is None or max_depth > 0:
        # Recurse into composite objects
        next_max_depth = None if max_depth is None else max_depth - 1
        if isinstance(obj, (tuple, list, set)):
            if max_length is None or len(obj) <= max_length:
                return type(obj)(deep_copy_and_replace_quibs_with_vals(sub_obj, next_max_depth) for sub_obj in obj)
        elif isinstance(obj, slice):
            return slice(deep_copy_and_replace_quibs_with_vals(obj.start, next_max_depth),
                         deep_copy_and_replace_quibs_with_vals(obj.stop, next_max_depth),
                         deep_copy_and_replace_quibs_with_vals(obj.step, next_max_depth))
    return copy(obj)


def shallow_copy_and_replace_quibs_with_vals(obj: Any):
    """
    Deep copy `obj` while replacing quibs with their values, with a limited depth and length.
    """
    return deep_copy_and_replace_quibs_with_vals(obj, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH)


def copy_and_replace_quibs_with_vals(obj: Any):
    result = shallow_copy_and_replace_quibs_with_vals(obj)
    if is_debug():
        expected = deep_copy_and_replace_quibs_with_vals(obj)
        if expected != result:
            raise NestedQuibException.create_from_object(obj)
    return result


def iter_quibs_in_object_recursively(obj, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    """
    Returns an iterator for quib objects nested in the given python object.
    Quibs that appear more than once will not be repeated.
    When `max_depth` is given, limits the depth in which quibs are looked for.
    `max_depth=0` means only `obj` itself will be checked and replaced,
    `max_depth=1` means `obj` and all objects it directly references, and so on.
    When `max_length` is given, does not recurse into iterables larger than `max_length`.
    """
    from pyquibbler.quib import Quib
    quibs = set()
    if isinstance(obj, Quib):
        if obj not in quibs:
            quibs.add(obj)
            yield obj
    elif max_depth is None or max_depth > 0:
        # Recurse into composite objects
        if isinstance(obj, (tuple, list, set)):
            # This is a fixed-size collection
            if max_length is None or len(obj) <= max_length:
                # The collection is small enough
                next_max_depth = None if max_depth is None else max_depth - 1
                for sub_obj in obj:
                    yield from iter_quibs_in_object_recursively(sub_obj, next_max_depth, max_length)


def iter_quibs_in_object_shallowly(obj: Any):
    """
    Returns an iterator for quib objects nested within the given python object,
    with limited width and length while scanning for quibs.
    """
    return iter_quibs_in_object_recursively(obj, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH)


def iter_quibs_in_object(obj: Any):
    result = iter_quibs_in_object_shallowly(obj)
    if is_debug():
        collected_result = set(result)
        result = iter(collected_result)
        expected = set(iter_quibs_in_object_recursively(obj))
        if collected_result != expected:
            raise NestedQuibException(obj, set(expected))
    return result


def iter_quibs_in_args(args, kwargs):
    """
    Returns an iterator for all quib objects nested in the given args and kwargs.
    """
    return chain(*map(iter_quibs_in_object, chain(args, kwargs.values())))


def call_func_with_quib_values(func, args, kwargs):
    """
    Calls a function with the specified args and kwargs while replacing quibs with their values.
    """
    new_args = [copy_and_replace_quibs_with_vals(arg) for arg in args]
    kwargs = {name: copy_and_replace_quibs_with_vals(val) for name, val in kwargs.items()}
    return func(*new_args, **kwargs)


def call_method_with_quib_values(func, self, args, kwargs):
    """
    Calls an instance method with the specified args and kwargs while replacing quibs with their values.
    """
    return call_func_with_quib_values(func, [self, *args], kwargs)


def is_there_a_quib_in_object(obj):
    """
    Returns true if there is a quib object nested inside the given object and false otherwise.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj))


def is_there_a_quib_in_args(args, kwargs):
    """
    Returns true if there is a quib object nested inside the given args and kwargs and false otherwise.
    For use by function wrappers that need to determine if the underlying function was called with a quib.
    """
    return not is_iterator_empty(iter_quibs_in_args(args, kwargs))
