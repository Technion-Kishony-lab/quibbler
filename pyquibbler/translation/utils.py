from copy import copy
from typing import Callable, Any

from pyquibbler.utilities.iterators import SHALLOW_MAX_LENGTH, SHALLOW_MAX_DEPTH, recursively_run_func_on_object
from pyquibbler.translation.types import Source


def copy_and_replace_sources_with_vals(obj: Any):
    """
    Copy `obj` while replacing quibs with their values, with a limited depth and length.
    """
    from matplotlib.artist import Artist

    def replace_with_value_if_source_or_copy(o):
        if isinstance(o, Source):
            return o.value
        if isinstance(o, Artist):
            return o
        try:
            return copy(o)
        except NotImplementedError:
            return o

    result = recursively_run_func_on_object(func=replace_with_value_if_source_or_copy, max_depth=SHALLOW_MAX_DEPTH,
                                            max_length=SHALLOW_MAX_LENGTH, obj=obj)
    return result


def call_func_with_sources_values(func: Callable, args, kwargs):
    """
    Calls a function with the specified args and kwargs while replacing quibs with their values.
    """
    new_args = (tuple(copy_and_replace_sources_with_vals(arg) for arg in args))
    new_kwargs = {name: copy_and_replace_sources_with_vals(val) for name, val in kwargs.items()}
    return func(*new_args, **new_kwargs)
