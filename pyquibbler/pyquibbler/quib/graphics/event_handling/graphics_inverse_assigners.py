from __future__ import annotations

from pyquibbler.function_definitions import FuncArgsKwargs
from matplotlib.backend_bases import PickEvent, MouseEvent
from pyquibbler.quib.types import XY
from pyquibbler.assignment import OverrideGroup

from .graphics_inverse_assigner import graphics_inverse_assigner
from .graphics_inverse_assignment import get_override_group_by_indices
from .plt_plot_parser import get_xdata_arg_indices_and_ydata_arg_indices, get_data_number_and_index_from_artist_index


@graphics_inverse_assigner(['Axes.plot'])
def get_override_group_for_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent,
                                     func_args_kwargs: FuncArgsKwargs) -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.plot(...)`.
    """
    args = func_args_kwargs.args
    x_arg_indices, y_arg_indices, _ = get_xdata_arg_indices_and_ydata_arg_indices(args)
    artist_index = pick_event.artist._index_in_plot
    data_number, data_index = \
        get_data_number_and_index_from_artist_index(args, x_arg_indices, y_arg_indices, artist_index)
    x_arg_index = x_arg_indices[data_number]
    y_arg_index = y_arg_indices[data_number]
    x_arg = None if x_arg_index is None else args[x_arg_index]
    y_arg = args[y_arg_index]
    return get_override_group_by_indices(XY(x_arg, y_arg), data_index, pick_event, mouse_event)


@graphics_inverse_assigner(['Axes.scatter'])
def get_override_group_for_axes_scatter(pick_event: PickEvent, mouse_event: MouseEvent,
                                        func_args_kwargs: FuncArgsKwargs) -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.scatter(...)`.
    """
    args = func_args_kwargs.args
    return get_override_group_by_indices(XY(args[1], args[2]), None, pick_event, mouse_event)


FUNC_NAME_TO_ARGS = {
    'axvline': XY('x', None),
    'axhline': XY(None, 'y'),
}


@graphics_inverse_assigner([
    'Axes.axvline',
    'Axes.axhline',
])
def get_override_group_for_axes_lines(pick_event: PickEvent, mouse_event: MouseEvent,
                                      func_args_kwargs: FuncArgsKwargs) -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.scatter(...)`.
    """
    arg_names = FUNC_NAME_TO_ARGS[func_args_kwargs.func.__name__]
    args = XY.from_func(lambda z: None if z is None else func_args_kwargs.get(z), arg_names)
    return get_override_group_by_indices(args, None, pick_event, mouse_event)
