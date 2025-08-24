from copy import copy
from typing import Any

from pyquibbler.utilities.iterators import recursively_run_func_on_object

from .types import Source


def copy_and_replace_sources_with_vals(obj: Any, recurse_mode='deep') -> Any:
    """
    Copy `obj` while replacing quibs with their values, with a limited depth and length.
    """
    from matplotlib.artist import Artist
    from matplotlib.widgets import AxesWidget

    def replace_with_value_if_source_or_copy(o):
        if isinstance(o, Source):
            return o.value
        if isinstance(o, (Artist, AxesWidget)):
            return o
        try:
            return copy(o)
        except NotImplementedError:
            return o

    result = recursively_run_func_on_object(func=replace_with_value_if_source_or_copy, obj=obj,
                                            recurse_mode=recurse_mode)
    return result
