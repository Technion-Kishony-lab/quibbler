import numpy as np
from typing import Tuple, Any, List, Iterable
from matplotlib.backend_bases import PickEvent, MouseEvent

from .graphics_reverse_assigner import graphics_reverse_assigner
from ...assignment import Assignment, QuibWithAssignment


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
                                        indices_to_set: Any,
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
            # We want to support both single values and arrays, so we need to reverse assign
            # appropriately (not use index if it was a single number, index will be zero but that's irrelevant to us)
            assignment = Assignment(value=value, paths=[indices_to_set
                                                        if issubclass(quib.get_type(), Iterable)
                                                        else ...])
            quibs_with_assignments.append(QuibWithAssignment(quib=quib,
                                                             assignment=assignment))
    return quibs_with_assignments


@graphics_reverse_assigner('Axes.plot')
def get_quibs_with_assignments_for_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent,
                                             args: List[Any]) -> List[QuibWithAssignment]:
    # It's deprecated to use a non-tuple as a per-dimension index
    indices = pick_event.ind
    if isinstance(indices, np.ndarray):
        indices = tuple(indices)
    x_arg_indices, y_arg_indices = get_xdata_arg_indices_and_ydata_arg_indices(tuple(args))
    quibs_with_assignments = get_quibs_with_assignments_for_axes(args, x_arg_indices, indices, mouse_event.xdata)
    quibs_with_assignments.extend(get_quibs_with_assignments_for_axes(args, y_arg_indices, indices, mouse_event.ydata))
    return quibs_with_assignments
