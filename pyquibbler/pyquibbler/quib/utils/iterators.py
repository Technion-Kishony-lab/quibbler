from typing import Optional

from pyquibbler.utilities.general_utils import Args, Kwargs
from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_recursively, iter_objects_of_type_in_object, \
    iter_object_type_in_args_kwargs


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
    from pyquibbler.quib.quib import Quib
    return iter_objects_of_type_in_object_recursively(Quib, obj, max_depth, max_length)


def iter_quibs_in_object(obj, recursive: bool = False):
    from pyquibbler.quib.quib import Quib
    return iter_objects_of_type_in_object(Quib, obj, recursive)


def iter_quibs_in_args(args: Args, kwargs: Kwargs):
    """
    Returns an iterator for all quib objects nested in the given args and kwargs.
    """
    from pyquibbler.quib.quib import Quib
    return iter_object_type_in_args_kwargs(Quib, args, kwargs)
