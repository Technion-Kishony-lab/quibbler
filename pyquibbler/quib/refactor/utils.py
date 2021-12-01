from copy import copy
from typing import Any, Optional

from pyquibbler.iterators import is_iterator_empty
from pyquibbler.quib.refactor.iterators import iter_quibs_in_object, iter_quibs_in_args, recursively_run_func_on_object


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
        from pyquibbler.quib.refactor.quib import Quib
        if isinstance(o, (Quib, Artist, AxesWidget)):
            return o
        return copy(o)

    return recursively_run_func_on_object(func=copy_if_not_quib_or_artist, max_length=max_length,
                                          max_depth=max_depth, obj=obj)

