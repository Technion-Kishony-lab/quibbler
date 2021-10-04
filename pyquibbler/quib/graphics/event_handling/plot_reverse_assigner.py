from typing import Tuple, Any, List, TYPE_CHECKING
from matplotlib.backend_bases import PickEvent, MouseEvent

from .graphics_reverse_assigner import graphics_reverse_assigner
from .utils import assign_data

if TYPE_CHECKING:
    from pyquibbler.quib.graphics.graphics_function_quib import GraphicsFunctionQuib


def get_xdata_arg_indices_and_ydata_arg_indices(args: Tuple[Any, ...]):
    """
    Gets a list of indices of arguments referencing `xdata`s, and a list of indices of arguments referencing `ydata`

    There are a few options for how arguments can be built for plot

    A. (ydata)
    B. (ydata, fmt)
    C. (xdata, ydata, [fmt], xdata, ydata...)

    Where C above is essentially a combination of cases where fmt is optional
    """

    x_data_arg_indexes = []
    y_data_arg_indexes = []

    # We have `self` (Axes) as arg 0

    if len(args) == 2:
        return [], [1]

    if len(args) == 3:
        if isinstance(args[2], str):
            return [], [1]

    i = 1
    while i < len(args):
        step = 2
        potential_fmt_index = i + 2
        if potential_fmt_index < len(args) and isinstance(args[potential_fmt_index], str):
            step += 1
        x_data_arg_indexes.append(i)
        y_data_arg_indexes.append(i + 1)

        i += step

    return x_data_arg_indexes, y_data_arg_indexes


def assign_data_for_axes(function_quib: 'GraphicsFunctionQuib',
                         arg_indices: List[int],
                         indices_to_set: Any,
                         value: Any):
    """
    Assign data for an axes (x or y) to all relevant quib args
    """
    from pyquibbler.quib import Quib
    # mouse_event.xdata and mouse_event.ydata can be None if the mouse is outside the figure
    if value is None:
        return

    for arg_index in arg_indices:
        if isinstance(function_quib.args[arg_index], Quib):
            assign_data(function_quib.args[arg_index], indices_to_set, value)


@graphics_reverse_assigner('Axes.plot')
def reverse_assign_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent,
                             function_quib: 'GraphicsFunctionQuib') -> None:
    indices = pick_event.ind
    x_arg_indices, y_arg_indices = get_xdata_arg_indices_and_ydata_arg_indices(function_quib.args)
    assign_data_for_axes(function_quib, x_arg_indices, indices, mouse_event.xdata)
    assign_data_for_axes(function_quib, y_arg_indices, indices, mouse_event.ydata)
