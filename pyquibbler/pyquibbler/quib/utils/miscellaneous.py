from copy import copy
from typing import Any

from attr.validators import max_len

from pyquibbler.utilities.iterators import is_iterator_empty, recursively_run_func_on_object
from .iterators import iter_quibs_in_object


def is_there_a_quib_in_object(obj) -> bool:
    """
    Returns true if there is a quib object nested inside the given object.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj))


def deep_copy_without_quibs_or_graphics(obj: Any, recurse_mode='deep'):
    from matplotlib.artist import Artist
    from matplotlib.widgets import AxesWidget
    from pyquibbler.quib.quib import Quib

    def copy_if_not_quib_or_artist(o):
        if isinstance(o, (Quib, Artist, AxesWidget)) or callable(o):
            return o
        return copy(o)

    return recursively_run_func_on_object(func=copy_if_not_quib_or_artist, obj=obj, recurse_mode=recurse_mode,
                                          iterate_on_attributes=False)


def copy_and_replace_quibs_with_vals(obj: Any, recurse_mode='deep',
                                     max_depth: int = None, max_length: int = None) -> Any:
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

    result = recursively_run_func_on_object(
        func=replace_with_value_if_quib_or_copy,
        obj=obj, recurse_mode=recurse_mode, max_depth=max_depth, max_length=max_length)
    return result
