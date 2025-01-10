from __future__ import annotations

from matplotlib.backend_bases import MouseEvent
from pyquibbler.assignment import OverrideGroup
from .enhance_pick_event import EnhancedPickEventWithFuncArgsKwargs

from .graphics_inverse_assigner import graphics_inverse_assigner
from .graphics_inverse_assignment import GetOverrideGroupFromGraphics
from .plt_plot_parser import get_xdata_arg_indices_and_ydata_arg_indices, get_data_number_and_index_from_artist_index
from .utils import skip_vectorize


@graphics_inverse_assigner(['Axes.plot'])
def get_override_group_for_axes_plot(enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs,
                                     mouse_event: MouseEvent) -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.plot(...)`.
    """
    args = enhanced_pick_event.func_args_kwargs.args
    x_arg_indices, y_arg_indices, _ = get_xdata_arg_indices_and_ydata_arg_indices(args)
    artist_index = enhanced_pick_event.artist._index_in_plot
    data_number, data_index = \
        get_data_number_and_index_from_artist_index(args, x_arg_indices, y_arg_indices, artist_index)
    x_arg_index = x_arg_indices[data_number]
    y_arg_index = y_arg_indices[data_number]
    x_arg = None if x_arg_index is None else args[x_arg_index]
    y_arg = args[y_arg_index]
    return GetOverrideGroupFromGraphics((x_arg, y_arg), data_index, enhanced_pick_event, mouse_event).get_overrides()


@graphics_inverse_assigner(['Axes.scatter'])
def get_override_group_for_axes_scatter(enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs,
                                        mouse_event: MouseEvent) -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.scatter(...)`.
    """
    args = enhanced_pick_event.func_args_kwargs.args
    return GetOverrideGroupFromGraphics((args[1], args[2]), None, enhanced_pick_event, mouse_event).get_overrides()


FUNC_NAME_TO_ARGS = {
    'axvline': ('x', None),
    'axhline': (None, 'y'),
}


@graphics_inverse_assigner([
    'Axes.axvline',
    'Axes.axhline',
])
def get_override_group_for_axes_lines(enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs,
                                      mouse_event: MouseEvent) -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.scatter(...)`.
    """
    func_args_kwargs = enhanced_pick_event.func_args_kwargs
    arg_names = FUNC_NAME_TO_ARGS[func_args_kwargs.func.__name__]
    args = skip_vectorize(func_args_kwargs.get)(arg_names)
    return GetOverrideGroupFromGraphics(args, None, enhanced_pick_event, mouse_event).get_overrides()
