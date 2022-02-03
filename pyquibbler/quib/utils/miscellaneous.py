from copy import copy
from typing import Any, Optional, Tuple, Callable, Dict

from pyquibbler.env import DEBUG
from pyquibbler.utilities.iterators import is_iterator_empty, iter_args_and_names_in_function_call, \
    SHALLOW_MAX_LENGTH, SHALLOW_MAX_DEPTH, recursively_run_func_on_object
from .iterators import iter_quibs_in_object, iter_quibs_in_args, iter_quibs_in_object_recursively
from ..exceptions import NestedQuibException
from ...path import Path


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


def get_nested_quibs_by_arg_names_in_function_call(func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any]):
    """
    Look for erroneously nested quibs in a function call and return a mapping between arg names and the quibs they
    have nested inside them.
    """
    nested_quibs_by_arg_names = {}
    for name, val in iter_args_and_names_in_function_call(func, args, kwargs, False):
        quibs = set(iter_quibs_in_object_recursively(val))
        if quibs:
            nested_quibs_by_arg_names[name] = quibs
    return nested_quibs_by_arg_names


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


def get_user_friendly_name_for_requested_valid_path(valid_path: Optional[Path]):
    """
    Get a user-friendly name representing the call to get_value_valid_at_path
    """
    if valid_path is None:
        return 'get_blank_value()'
    elif len(valid_path) == 0:
        return 'get_value()'
    else:
        return f'get_value_valid_at_path({valid_path})'


class NoValue:
    pass
