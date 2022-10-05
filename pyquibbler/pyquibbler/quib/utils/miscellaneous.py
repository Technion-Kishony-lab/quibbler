from copy import copy
from typing import Any, Optional

from pyquibbler.env import DEBUG
from pyquibbler.utilities.iterators import is_iterator_empty, recursively_run_func_on_object, \
    SHALLOW_MAX_LENGTH, SHALLOW_MAX_DEPTH
from .iterators import iter_quibs_in_object, iter_quibs_in_args, iter_quibs_in_object_recursively
from ..exceptions import NestedQuibException


def is_there_a_quib_in_object(obj, recursive: bool = False):
    """
    Returns true if there is a quib object nested inside the given object.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj, recursive))


def is_there_a_quib_in_args(args, kwargs):
    """
    Returns true if there is a quib object nested inside the given args and kwargs and false otherwise.
    For use by function wrappers that need to determine if the underlying function was called with a quib.
    """
    return not is_iterator_empty(iter_quibs_in_args(args, kwargs))


def deep_copy_without_quibs_or_graphics(obj: Any, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    from matplotlib.artist import Artist
    from matplotlib.widgets import AxesWidget
    from pyquibbler.quib.quib import Quib

    def copy_if_not_quib_or_artist(o):
        if isinstance(o, (Quib, Artist, AxesWidget)) or callable(o):
            return o
        return copy(o)

    return recursively_run_func_on_object(func=copy_if_not_quib_or_artist, max_length=max_length,
                                          max_depth=max_depth, obj=obj)


def copy_and_replace_quibs_with_vals(obj: Any):
    """
    Copy `obj` while replacing quibs with their values, with a limited depth and length.
    """
    from pyquibbler.quib.quib import Quib
    from matplotlib.widgets import AxesWidget
    from matplotlib.artist import Artist

    def replace_with_value_if_quib_or_copy(o):
        if isinstance(o, Quib):
            return o.get_value()
        if isinstance(o, (Artist, AxesWidget)):
            return o
        try:
            return copy(o)
        except NotImplementedError:
            return o

    result = recursively_run_func_on_object(func=replace_with_value_if_quib_or_copy, max_depth=SHALLOW_MAX_DEPTH,
                                            max_length=SHALLOW_MAX_LENGTH, obj=obj)
    if DEBUG:
        nested_quibs = set(iter_quibs_in_object_recursively(result))
        if is_there_a_quib_in_object(result, recursive=True):
            raise NestedQuibException(obj, nested_quibs)
    return result
