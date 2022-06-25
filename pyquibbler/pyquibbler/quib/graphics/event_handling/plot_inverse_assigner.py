from collections import defaultdict
from typing import Any, List, Tuple, Union
from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton

from pyquibbler.assignment.override_choice import get_override_group_for_quib_changes
from pyquibbler.path import PathComponent
from pyquibbler.assignment import AssignmentToQuib, Assignment
from .graphics_inverse_assigner import graphics_inverse_assigner
from pyquibbler.assignment import OverrideGroup

from numpy import unravel_index


def get_xdata_arg_indices_and_ydata_arg_indices(args: Tuple[List, List]):
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


def get_quibs_to_paths_affected_by_event(args: List[Any], arg_indices: List[int], artist_index: int, data_indices: Any):
    from pyquibbler.quib import Quib
    quibs_to_paths = defaultdict(list)
    for arg_index in arg_indices:
        quib = args[arg_index]
        if isinstance(quib, Quib):
            # Support indexing of lists when more than one marker is dragged
            for data_index in data_indices:
                shape = quib.get_shape()
                if artist_index is not None:
                    # for plot:
                    if len(shape) == 0:
                        path = []
                    elif len(shape) == 1:
                        path = [PathComponent(quib.get_type(), data_index)]
                    else:
                        assert len(shape) == 2, 'Matplotlib is not supposed to support plotting 3d data'
                        path = [PathComponent(quib[0].get_type(), data_index),
                                # Plot args should be array-like, so quib[0].get_type() should be representative
                                PathComponent(quib.get_type(), artist_index)]
                else:
                    # for scatter:
                    path = [PathComponent(quib.get_type(), unravel_index(data_index, shape))]
                quibs_to_paths[quib].append(path)
    return quibs_to_paths


def get_overrides_for_event(args: List[Any], arg_indices: List[int], artist_index: int, data_indices: Any, value: Any):
    """
    Assign data for an axes (x or y) to all relevant quib args
    """
    # mouse_event.xdata and mouse_event.ydata can be None if the mouse is outside the figure
    if value is None:
        return []

    quibs_to_paths = get_quibs_to_paths_affected_by_event(args, arg_indices, artist_index, data_indices)
    return [AssignmentToQuib(quib, Assignment(value=value, path=path))
            for quib, paths in quibs_to_paths.items() for path in paths]


def get_override_removals_for_event(args: List[Any], arg_indices: List[int], artist_index: int, data_indices: Any):
    """
    Assign data for an axes (x or y) to all relevant quib args
    """
    quibs_to_paths = get_quibs_to_paths_affected_by_event(args, arg_indices, artist_index, data_indices)
    return [AssignmentToQuib(quib, Assignment.create_default(path))
            for quib, paths in quibs_to_paths.items() for path in paths]


def get_override_group_by_indices(x_arg_indices: List[int], y_arg_indices: List[int], artist_index: Union[None, int],
                                  pick_event: PickEvent, mouse_event: MouseEvent, args: List[Any]) -> OverrideGroup:
    indices = pick_event.ind
    if pick_event.mouseevent.button is MouseButton.RIGHT:
        arg_indices = x_arg_indices + y_arg_indices
        changes = get_override_removals_for_event(args, arg_indices, artist_index, indices)
    else:
        changes = [*get_overrides_for_event(args, x_arg_indices, artist_index, indices, mouse_event.xdata),
                   *get_overrides_for_event(args, y_arg_indices, artist_index, indices, mouse_event.ydata)]
    return get_override_group_for_quib_changes(changes)


@graphics_inverse_assigner(['Axes.plot'])
def get_override_group_for_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent, args: List[Any]) \
        -> OverrideGroup:
    x_arg_indices, y_arg_indices = get_xdata_arg_indices_and_ydata_arg_indices(tuple(args))
    artist_index = pick_event.artist._index_in_plot
    return get_override_group_by_indices(x_arg_indices, y_arg_indices, artist_index, pick_event, mouse_event, args)


@graphics_inverse_assigner(['Axes.scatter'])
def get_override_group_for_axes_scatter(pick_event: PickEvent, mouse_event: MouseEvent, args: List[Any]) \
        -> OverrideGroup:
    x_arg_indices, y_arg_indices = [1], [2]
    artist_index = None
    return get_override_group_by_indices(x_arg_indices, y_arg_indices, artist_index, pick_event, mouse_event, args)
