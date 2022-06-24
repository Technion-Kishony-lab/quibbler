from copy import copy
from typing import Any, Optional

from pyquibbler.env import DEBUG
from pyquibbler.utilities.iterators import is_iterator_empty, \
    SHALLOW_MAX_LENGTH, SHALLOW_MAX_DEPTH, recursively_run_func_on_object
from .iterators import iter_quibs_in_object, iter_quibs_in_args, iter_quibs_in_object_recursively
from ..exceptions import NestedQuibException
from ...assignment.default_value import Default


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


def deep_copy_without_quibs_or_graphics(obj: Any, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    from matplotlib.artist import Artist

    def copy_if_not_quib_or_artist(o):
        from matplotlib.widgets import AxesWidget
        from pyquibbler.quib.quib import Quib
        if isinstance(o, (Quib, Artist, AxesWidget)):
            return o
        return copy(o)

    return recursively_run_func_on_object(func=copy_if_not_quib_or_artist, max_length=max_length,
                                          max_depth=max_depth, obj=obj)


def copy_and_replace_quibs_with_vals(obj: Any):
    """
    Copy `obj` while replacing quibs with their values, with a limited depth and length.
    """
    from pyquibbler.quib.quib import Quib
    from matplotlib.artist import Artist

    def replace_with_value_if_quib_or_copy(o):
        if isinstance(o, Quib):
            return o.get_value()
        if isinstance(o, Artist):
            return o
        try:
            return copy(o)
        except NotImplementedError:
            return o

    result = recursively_run_func_on_object(func=replace_with_value_if_quib_or_copy, max_depth=SHALLOW_MAX_DEPTH,
                                            max_length=SHALLOW_MAX_LENGTH, obj=obj)
    if DEBUG:
        nested_quibs = set(iter_quibs_in_object_recursively(result))
        if nested_quibs:
            raise NestedQuibException(obj, nested_quibs)
    return result


class NoValue:
    pass


def is_saveable_as_txt(val: Any) -> bool:
    all_ok = True

    def set_false_if_repr_is_not_invertible(v):
        from numpy import ndarray, int64, int32, bool_
        nonlocal all_ok
        all_ok &= isinstance(v, (Default, bool, str, int, float, ndarray, slice, type(None), int64, int32, bool_))

    # TODO: for dicts we need to check also that the keys are saveable
    recursively_run_func_on_object(func=set_false_if_repr_is_not_invertible, obj=val)
    return all_ok
