from __future__ import annotations

import numpy as np

from functools import partial
from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton

from typing import Any, List, Tuple, Union, Optional

from pyquibbler.utilities.general_utils import Args

from pyquibbler.assignment import get_axes_x_y_tolerance, create_assignment, OverrideGroup, \
    get_override_group_for_quib_changes, AssignmentToQuib, Assignment, default
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.path import PathComponent, Path, deep_get
from pyquibbler.utilities.numpy_original_functions import np_shape

from .graphics_inverse_assigner import graphics_inverse_assigner

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


ArgIndices = List[Optional[int]]


def _is_arg_str(arg):
    from pyquibbler.quib.quib import Quib
    if isinstance(arg, Quib):
        arg = arg.get_value()
    return isinstance(arg, str)


def get_xdata_arg_indices_and_ydata_arg_indices(args: Args) -> Tuple[ArgIndices, ArgIndices, ArgIndices]:
    """
    Gets three same-length lists of indices of arguments referencing `xdata` and `ydata` and 'fmt' of a plot command

    xdata indices and fmt indices can be None

    There are a few options for how arguments can be built for plot

    A. (ydata)
    B. (ydata, fmt, ...)
    C. (xdata, ydata, ...)
    D. (xdata, ydata, fmt, ...)

    """

    x_data_arg_indices = []
    y_data_arg_indices = []
    fmt_indices = []

    # We have `self` (Axes) as arg 0
    i = 1

    while i < len(args):
        number_of_remaining_args = len(args) - i
        i0, i1, i2 = i, i + 1, i + 2
        if number_of_remaining_args == 1:
            # ydata
            xyf_indices = None, i0, None
            i += 1
        elif _is_arg_str(args[i1]):
            # ydata, fmt
            xyf_indices = None, i0, i1
            i += 2
        elif number_of_remaining_args == 2 or not _is_arg_str(args[i2]):
            # xdata, ydata
            xyf_indices = i0, i1, None
            i += 2
        else:
            # xdata, ydata, fmt
            xyf_indices = i0, i1, i2
            i += 3

        x_data_arg_indices.append(xyf_indices[0])
        y_data_arg_indices.append(xyf_indices[1])
        fmt_indices.append(xyf_indices[2])

    return x_data_arg_indices, y_data_arg_indices, fmt_indices


def _get_number_of_columns(arg: Any):
    """
    Return size at axis=1. if less than 2 dimensions, return 1.
    This is the number of artists produced by plot for this arg.
    """
    from pyquibbler.quib.quib import Quib
    if isinstance(arg, Quib):
        shape = arg.get_shape()
    else:
        shape = np_shape(arg)
    if len(shape) < 2:
        return 1
    return shape[1]


def get_data_number_and_index_from_artist_index(args: Args, x_data_arg_indices, y_data_arg_indices, artist_index: int
                                                ) -> Tuple[int, int]:
    data_number = -1
    total_number_of_artists = 0
    while artist_index >= total_number_of_artists:
        data_number += 1
        y_index = y_data_arg_indices[data_number]
        num_columns_y = _get_number_of_columns(args[y_index])
        x_index = x_data_arg_indices[data_number]
        if x_index is None:
            num_artists = num_columns_y
        else:
            num_columns_x = _get_number_of_columns(args[x_index])
            num_artists = num_columns_x if num_columns_y == 1 else num_columns_y  # broadcast
        total_number_of_artists += num_artists
    return data_number, artist_index - (total_number_of_artists - num_artists)


def get_quibs_and_paths_affected_by_event(arg: Any, data_index: Optional[int], point_indices: List[int]
                                          ) -> List[Tuple[Quib, Path]]:
    from pyquibbler.quib.quib import Quib
    quibs_and_paths = []
    for point_index in point_indices:
        if isinstance(arg, Quib):
            # Support indexing of lists when more than one marker is dragged
            shape = arg.get_shape()
            if data_index is not None:
                # plt.plot:
                if len(shape) == 0:
                    path = []
                elif len(shape) == 1:
                    path = [PathComponent(point_index)]
                elif len(shape) == 2:
                    path = [
                        PathComponent(point_index),
                        PathComponent(0 if shape[1] == 1 else data_index)  # de-broadcast if needed
                    ]
                else:
                    assert False, 'Matplotlib is not supposed to support plotting data arguments with >2 dimensions'
            else:
                # plt.scatter:
                path = [PathComponent(np.unravel_index(point_index, shape))]
            quibs_and_paths.append((arg, path))
            continue
        if isinstance(arg, list):
            quib = arg[data_index]
            if isinstance(quib, Quib):
                quibs_and_paths.append((quib, []))
                continue
        quibs_and_paths.append((None, None))

    return quibs_and_paths


def get_overrides_for_event(arg: Any, data_index: Optional[int], point_indices: List[int],
                            value: Any = default, tolerance: Any = None,
                            ) -> List[Optional[AssignmentToQuib]]:
    """
    Assign mouse coordinate (x or y) to corresponding arg
    """
    quibs_and_paths = get_quibs_and_paths_affected_by_event(arg, data_index, point_indices)
    overrides = []
    for quib, path in quibs_and_paths:
        if quib is None or value is None:
            # mouse_event.xdata and mouse_event.ydata can be None if the mouse is outside the figure
            override = None
        else:
            if value is default:
                assignment = Assignment.create_default(path)
            else:
                current_value = deep_get(quib.handler.get_value_valid_at_path(path), path)
                # we cast value and the tolerance by current value. so datetime or int work as expected:
                assignment = create_assignment(value, path, tolerance,
                                               convert_func=partial(convert_scalar_value, current_value))
            override = AssignmentToQuib(quib, assignment)
        overrides.append(override)
    return overrides


def get_override_group_by_indices(x_arg: Any, y_arg: Any, data_index: Union[None, int],
                                  pick_event: PickEvent, mouse_event: MouseEvent) -> OverrideGroup:
    point_indices = pick_event.ind
    if pick_event.mouseevent.button is MouseButton.RIGHT:
        changes_x = get_overrides_for_event(x_arg, data_index, point_indices, default)
        changes_y = get_overrides_for_event(y_arg, data_index, point_indices, default)
    else:
        tolerance_x, tolerance_y = get_axes_x_y_tolerance(pick_event.artist.axes)
        changes_x = get_overrides_for_event(x_arg, data_index, point_indices, mouse_event.xdata, tolerance_x)
        changes_y = get_overrides_for_event(y_arg, data_index, point_indices, mouse_event.ydata, tolerance_y)
    changes = changes_x + changes_y
    changes = [change for change in changes if change if not None]
    return get_override_group_for_quib_changes(changes)


@graphics_inverse_assigner(['Axes.plot'])
def get_override_group_for_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent, args: Args) \
        -> OverrideGroup:
    x_arg_indices, y_arg_indices, _ = get_xdata_arg_indices_and_ydata_arg_indices(args)
    artist_index = pick_event.artist._index_in_plot
    data_number, data_index = \
        get_data_number_and_index_from_artist_index(args, x_arg_indices, y_arg_indices, artist_index)
    x_arg_index = x_arg_indices[data_number]
    y_arg_index = y_arg_indices[data_number]
    x_arg = None if x_arg_index is None else args[x_arg_index]
    y_arg = args[y_arg_index]
    return get_override_group_by_indices(x_arg, y_arg, data_index, pick_event, mouse_event)


@graphics_inverse_assigner(['Axes.scatter'])
def get_override_group_for_axes_scatter(pick_event: PickEvent, mouse_event: MouseEvent, args: Args) \
        -> OverrideGroup:
    return get_override_group_by_indices(args[1], args[2], None, pick_event, mouse_event)
