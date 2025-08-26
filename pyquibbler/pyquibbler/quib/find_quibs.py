from __future__ import annotations

from copy import copy
from typing import Any, List, TYPE_CHECKING

from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget

from pyquibbler.env import QUIB_SEARCH_PARAMS
from pyquibbler.utilities.general_utils import Args, Kwargs
from pyquibbler.utilities.iterators import recursively_run_func_on_object, iter_objects_of_type_in_object_recursively, \
    is_iterator_empty

if TYPE_CHECKING:
    from pyquibbler.function_definitions.location import SourceLocation


def get_quib_search_params(search_in_attributes):
    return QUIB_SEARCH_PARAMS if search_in_attributes else {**QUIB_SEARCH_PARAMS, 'max_depth_on_attributes': -1}


def deep_copy_without_graphics(obj: Any, action_on_quibs, search_in_attributes=False) -> Any:
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

        if isinstance(o, Quib):
            match action_on_quibs:
                case 'value':
                    return o.get_value()
                case 'keep':
                    return o
                case 'raise':
                    raise ValueError("Quib found in object where quibs are not allowed")
                case _:
                    raise ValueError(f"action_on_quibs must be 'keep' or 'val', 'raise'. Got '{action_on_quibs}'.")
        try:
            return copy(o)
        except NotImplementedError:
            return o

    return recursively_run_func_on_object(func=replace, obj=obj, **get_quib_search_params(search_in_attributes))



def get_quibs_or_sources_locations_in_args_kwargs(object_type, args: Args, kwargs: Kwargs,
                                                  search_in_attributes: bool = False) -> List[SourceLocation]:
    from pyquibbler.function_definitions.location import get_object_type_locations_in_args_kwargs
    return get_object_type_locations_in_args_kwargs(object_type, args, kwargs,
                                                    get_quib_search_params(search_in_attributes))


def iter_quibs_or_sources_in_object(obj, type_: type = None, search_in_attributes=False):
    if type_ is None:
        from pyquibbler.quib.quib import Quib
        type_ = Quib
    yield from iter_objects_of_type_in_object_recursively(type_, obj, **get_quib_search_params(search_in_attributes))


def is_there_a_quib_in_object(obj) -> bool:
    """
    Returns true if there is a quib object nested inside the given object.
    """
    return not is_iterator_empty(iter_quibs_or_sources_in_object(obj))
