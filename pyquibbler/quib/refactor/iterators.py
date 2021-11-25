import functools
import itertools
from typing import Optional, Type, Any, Mapping, Tuple

# Most common use-cases require one level of scanning - for example a quib inside a shape tuple.
# But there is also the case of indexing with quibs, like so: arr[q1:,q2:] which creates a quib inside a slice inside a
# tuple, which requires two levels of scanning.
from pyquibbler.env import DEBUG
from pyquibbler.quib.utils import NestedQuibException, QuibRef

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


def iter_quibs_in_object(obj, force_recursive: bool = False):
    from pyquibbler.quib.refactor.quib import Quib
    return iter_objects_of_type_in_object(Quib, obj, force_recursive)


def iter_object_type_in_args(object_type, args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Returns an iterator for all objects of a type nested in the given args and kwargs.
    """
    return itertools.chain(*map(functools.partial(iter_objects_of_type_in_object, object_type),
                                itertools.chain(args, kwargs.values())))


def iter_quibs_in_args(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Returns an iterator for all quib objects nested in the given args and kwargs.
    """
    from pyquibbler.quib.refactor.quib import Quib
    return iter_object_type_in_args(Quib, args, kwargs)
