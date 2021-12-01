import functools
import itertools
from typing import Optional, Type, Any, Mapping, Tuple, Callable

# Most common use-cases require one level of scanning - for example a quib inside a shape tuple.
# But there is also the case of indexing with quibs, like so: arr[q1:,q2:] which creates a quib inside a slice inside a
# tuple, which requires two levels of scanning.
from pyquibbler.iterators import iter_objects_of_type_in_object_recursively, iter_objects_of_type_in_object, \
    iter_object_type_in_args

SHALLOW_MAX_DEPTH = 2
SHALLOW_MAX_LENGTH = 100


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


def iter_quibs_in_object(obj, force_recursive: bool = False):
    from pyquibbler.quib.refactor.quib import Quib
    return iter_objects_of_type_in_object(Quib, obj, force_recursive)


def iter_quibs_in_args(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Returns an iterator for all quib objects nested in the given args and kwargs.
    """
    from pyquibbler.quib.refactor.quib import Quib
    return iter_object_type_in_args(Quib, args, kwargs)


def recursively_run_func_on_object(func: Callable, obj: Any,
                                   max_depth: Optional[int] = None, max_length: Optional[int] = None,
                                   iterable_func: Callable = None, slice_func: Callable = None):
    iterable_func = iterable_func if iterable_func is not None else lambda l: l
    slice_func = slice_func if slice_func is not None else lambda s: s
    if max_depth is None or max_depth > 0:
        # Recurse into composite objects
        next_max_depth = None if max_depth is None else max_depth - 1

        if isinstance(obj, (tuple, list, set)):
            if max_length is None or len(obj) <= max_length:
                return iterable_func(type(obj)((recursively_run_func_on_object(func, sub_obj, next_max_depth)
                                                for sub_obj in obj)))
        elif isinstance(obj, slice):
            return slice_func(slice(recursively_run_func_on_object(func, obj.start, next_max_depth),
                                    recursively_run_func_on_object(func, obj.stop, next_max_depth),
                                    recursively_run_func_on_object(func, obj.step, next_max_depth)))
    return func(obj)

