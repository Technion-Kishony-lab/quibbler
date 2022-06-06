from typing import Optional, Any, Mapping, Tuple

from pyquibbler.function_definitions import PositionalSourceLocation, KeywordSourceLocation
from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_recursively, iter_objects_of_type_in_object, \
    iter_object_type_in_args_kwargs, get_paths_for_objects_of_type


# Most common use-cases require one level of scanning - for example a quib inside a shape tuple.
# But there is also the case of indexing with quibs, like so: arr[q1:,q2:] which creates a quib inside a slice inside a
# tuple, which requires two levels of scanning.
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
    from pyquibbler.quib.quib import Quib
    return iter_objects_of_type_in_object(Quib, obj, force_recursive)


def iter_quibs_in_args(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Returns an iterator for all quib objects nested in the given args and kwargs.
    """
    from pyquibbler.quib.quib import Quib
    return iter_object_type_in_args_kwargs(Quib, args, kwargs)


def get_quib_locations_in_args_kwargs(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Find all quibns in args and kwargs and return their locations
    """
    from pyquibbler.quib.quib import Quib

    positional_locations = [PositionalSourceLocation(path[0], path[1:]) for
                            path in get_paths_for_objects_of_type(args, Quib)]

    keyword_locations = [KeywordSourceLocation(path[0], path[1:]) for
                            path in get_paths_for_objects_of_type(kwargs, Quib)]

    return positional_locations + keyword_locations
