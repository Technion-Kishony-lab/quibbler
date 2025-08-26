from copy import copy
from typing import Any

from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget

from pyquibbler.utilities.iterators import is_iterator_empty, recursively_run_func_on_object
from .iterators import iter_quibs_in_object


def is_there_a_quib_in_object(obj) -> bool:
    """
    Returns true if there is a quib object nested inside the given object.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj))


def deep_copy_without_graphics(obj: Any, action_on_quibs, recurse_mode='deep',
                               max_depth_on_object_arrays=-1, max_depth_on_attributes=-1):
    """
    Deep copies the given object, except for matplotlib Artists and AxesWidgets, which are returned as is.
    Quibs are handled according to action_on_quibs:
    - 'value' - replace quibs with their current value
    - 'keep' - keep quibs as is
    - 'raise' - raise an exception if a quib is found
    """
    from pyquibbler.quib.quib import Quib

    def replace(o):
        if isinstance(o, (Artist, AxesWidget)) or callable(o):
            return o
        if action_on_quibs == 'keep' and isinstance(o, Quib):
            return o

        if isinstance(o, Quib):
            if action_on_quibs == 'value':
                return o.get_value()
            elif action_on_quibs == 'keep':
                return o
            elif action_on_quibs == 'raise':
                raise ValueError("Quib found in object where quibs are not allowed")
            else:
                raise ValueError(f"action_on_quibs must be 'keep' or 'val', 'raise'. Got '{action_on_quibs}'.")
        try:
            return copy(o)
        except NotImplementedError:
            return o

    return recursively_run_func_on_object(func=replace, obj=obj, recurse_mode=recurse_mode,
                                          max_depth_on_object_arrays=max_depth_on_object_arrays,
                                          max_depth_on_attributes=max_depth_on_attributes)
