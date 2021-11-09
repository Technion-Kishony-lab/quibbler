from typing import Any, List, Tuple
from matplotlib.backend_bases import PickEvent, MouseEvent

from .graphics_inverse_assigner import graphics_inverse_assigner
from ...assignment import Assignment, QuibWithAssignment, PathComponent


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


def get_quibs_with_assignments_for_axes(args: List[Any],
                                        arg_indices: List[int],
                                        artist_index: int,
                                        data_indices: Any,
                                        value: Any):
    """
    Assign data for an axes (x or y) to all relevant quib args
    """
    from pyquibbler.quib import Quib
    # mouse_event.xdata and mouse_event.ydata can be None if the mouse is outside the figure
    if value is None:
        return []

    quibs_with_assignments = []
    for arg_index in arg_indices:
        quib = args[arg_index]
        if isinstance(quib, Quib):
            # Support indexing of lists when more than one marker is dragged
            for data_index in data_indices:
                shape = quib.get_shape()
                if len(shape) == 0:
                    path = []
                elif len(shape) == 1:
                    path = [PathComponent(quib.get_type(), data_index)]
                else:
                    assert len(shape) == 2, 'Matplotlib is not supposed to support plotting 3d data'
                    path = [PathComponent(quib[0].get_type(), data_index),
                            # Plot args should be array-like, so quib[0].get_type() should be representative
                            PathComponent(quib.get_type(), artist_index)]
                assignment = Assignment(value=value, path=path)
                quibs_with_assignments.append(QuibWithAssignment(quib, assignment))
    return quibs_with_assignments


@graphics_inverse_assigner('Axes.plot')
def get_quibs_with_assignments_for_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent,
                                             args: List[Any]) -> List[QuibWithAssignment]:
    indices = pick_event.ind
    x_arg_indices, y_arg_indices = get_xdata_arg_indices_and_ydata_arg_indices(tuple(args))
    artist_index = pick_event.artist._index_in_plot
    return [*get_quibs_with_assignments_for_axes(args, x_arg_indices, artist_index, indices, mouse_event.xdata),
            *get_quibs_with_assignments_for_axes(args, y_arg_indices, artist_index, indices, mouse_event.ydata)]
