from __future__ import annotations

import numpy as np

from functools import partial

from matplotlib.axes import Axes
from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton

from typing import Any, List, Tuple, Union, Optional

from pyquibbler.quib.types import XY, PointXY
from pyquibbler.utilities.general_utils import Args

from pyquibbler.assignment import get_axes_x_y_tolerance, create_assignment, OverrideGroup, \
    get_override_group_for_quib_changes, AssignmentToQuib, Assignment, default, get_override_group_for_quib_change
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.path import PathComponent, Path, deep_get
from pyquibbler.utilities.numpy_original_functions import np_shape

from .graphics_inverse_assigner import graphics_inverse_assigner
from .utils import get_closest_point_on_line_in_axes

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


ArgIndices = List[Optional[int]]


def _get_override_group_for_quib_change_or_none(quib_change: Optional[AssignmentToQuib]) -> Optional[OverrideGroup]:
    return None if quib_change is None else get_override_group_for_quib_change(quib_change, should_raise=False)


def _get_xy_current_point_from_xy_change(xy_change: XY):
    return PointXY.from_func(lambda xy: xy.get_value_at_path(), xy_change)


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
    """
    Returns the x-y pair number (data_number) and their column (data_column) that correspond to a given artist_index
    produced by a plt.plot command.

    plt.plot(x0, y0, [fmt], x1, y1, [fmt], ...)

    x0, y0 are data_number=0
    x1, y1 are data_number=1
    etc

    for example,
    plt.plot(x34, y34, 'o', x7, y7, 'x', x52, y5, '.', x41, y47)
    where x34 is an array of shape = (3, 4)

    will create a list of 4 + 1 + 2 + 7 = 14 artists
    artist_index = 9 will yield:
        data_number = 3 (namely, x41, y47)
        column_index = 2 (it is created by the data in the column 2 of x41, y47. x is broadcasted)
    """
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
    column_index = artist_index - (total_number_of_artists - num_artists)
    return data_number, column_index


def get_quibs_and_paths_affected_by_event(arg: Any, data_index: Optional[int], point_indices: List[int]
                                          ) -> List[Optional[Tuple[Quib, Path]]]:
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
        quibs_and_paths.append(None)

    return quibs_and_paths


def get_assignment_from_quib_and_path(quib_and_path: Optional[Tuple[Quib, Path]],
                                      value: Any = default, tolerance: Any = None,
                                      ) -> Optional[AssignmentToQuib]:
    """
    Get assignments of mouse coordinate (x or y) to corresponding arg
    """
    if quib_and_path is None or value is None:
        # mouse_event.xdata and mouse_event.ydata can be None if the mouse is outside the figure
        return None
    quib, path = quib_and_path
    if value is default:
        assignment = Assignment.create_default(path)
    else:
        current_value = deep_get(quib.handler.get_value_valid_at_path(path), path)
        # we cast value and the tolerance by current value. so datetime or int work as expected:
        assignment = create_assignment(value, path, tolerance,
                                       convert_func=partial(convert_scalar_value, current_value))
    return AssignmentToQuib(quib, assignment)


def get_plot_arg_assignments_for_event(quibs_and_paths: List[Optional[Tuple[Quib, Path]]],
                                       value: Any = default, tolerance: Any = None,
                                       ) -> List[Optional[AssignmentToQuib]]:
    """
    Get assignments of mouse coordinate (x or y) to corresponding arg
    """
    return [get_assignment_from_quib_and_path(quib_and_path, value, tolerance) for quib_and_path in quibs_and_paths]


def get_override_group_by_indices(xy_args: XY, data_index: Union[None, int],
                                  pick_event: PickEvent, mouse_event: MouseEvent) -> OverrideGroup:
    """
    Get overrides for a mouse event for an artist created by a plt.plot command in correspondence with the
    `data_index` column of the given data arguments xy_args.x, xy_args.y.

    `data_index=None`: denotes artist produced by plt.scatter (where the x and y arguments are treated as flatten)

    the key here is to account for cases where dragging could be restricted to a curve, in which case we want to choose
    the point along the curve closest to the mouse.

    The function treats these 6 possibilities:

    1. x, y are not quibs
        dragging is disabled

    2. only x or only y are quibs:
        if x is a quib, assign mouse-x to it (if inversion is possible). (same for y)

    3. both x and y are quibs, but neither can be inverted.
        dragging is disabled

    4. both x and y are quibs, but only one can be inverted:
        get a drag-line by applying the inversion of the invertible quib
        and find the point on the line closest to the mouse and assign to the invertible quib.

    5. both x and y can be inverted, and the inversion of one affects the other.
        get the drag-line and invert to the closest point

    6. both x and y can be inverted without affecting each other.
        return the two inversions.

    only x or y are quibs, or because both are quibs and their values are dependent on the shared upstream override.
    """
    point_indices = pick_event.ind
    ax = pick_event.artist.axes
    quibs_and_paths = XY.from_func(get_quibs_and_paths_affected_by_event, xy_args, data_index, point_indices)

    if pick_event.mouseevent.button is MouseButton.RIGHT:
        changes = XY.from_func(get_plot_arg_assignments_for_event, quibs_and_paths, default)
        changes = [change for change in changes.x + changes.y if change is not None]
        return get_override_group_for_quib_changes(changes)

    tolerance = get_axes_x_y_tolerance(ax)
    xy_mouse = PointXY(mouse_event.xdata, mouse_event.ydata)
    if not isinstance(ax, Axes):
        # for testing
        changes = XY.from_func(get_plot_arg_assignments_for_event, quibs_and_paths, xy_mouse, tolerance)
        changes = [change for change in changes.x + changes.y if change is not None]
        return get_override_group_for_quib_changes(changes)

    all_overrides = OverrideGroup()
    for quib_and_path in [XY(quib_and_path_x, quib_and_path_y)
                             for quib_and_path_x, quib_and_path_y in zip(quibs_and_paths.x, quibs_and_paths.y)]:
        overrides = OverrideGroup()
        if quib_and_path.x is None and quib_and_path.y is None:
            # both x and y are not quibs
            continue
        elif quib_and_path.is_xor():
            # either only x is a quib or only y is a quib
            xy_change = XY.from_func(get_assignment_from_quib_and_path, quib_and_path, xy_mouse, tolerance)
            override = _get_override_group_for_quib_change_or_none(xy_change.get_value_not_none())
            overrides = override or overrides
        else:
            # both x and y are quibs:
            xy_change = XY.from_func(get_assignment_from_quib_and_path, quib_and_path, xy_mouse)
            xy_old = _get_xy_current_point_from_xy_change(xy_change)
            xy_assigned_value = PointXY.from_func(lambda xy: xy.assignment.value, xy_change)

            is_mouse_dx_larger_than_dy = \
                np.diff(np.abs(ax.transData.transform(xy_mouse) - ax.transData.transform(xy_old))) < 0
            xy_order = (0, 1) if is_mouse_dx_larger_than_dy else (1, 0)  # start with the larger mouse move
            for focal_xy in xy_order:
                other_xy = 1 - focal_xy
                focal_override = _get_override_group_for_quib_change_or_none(xy_change[focal_xy])
                if focal_override is None:
                    continue
                focal_override.apply(is_dragging=None)
                xy_new = _get_xy_current_point_from_xy_change(xy_change)
                xy_closest = get_closest_point_on_line_in_axes(ax, xy_old, xy_new, xy_assigned_value)
                adjusted_change = get_assignment_from_quib_and_path(quib_and_path[focal_xy], xy_closest[focal_xy],
                                                                    tolerance[focal_xy])
                overrides.extend(get_override_group_for_quib_change(adjusted_change))

                if xy_old[other_xy] != xy_new[other_xy]:
                    # x-y values are dependent
                    break
        all_overrides.extend(overrides)
    return all_overrides


@graphics_inverse_assigner(['Axes.plot'])
def get_override_group_for_axes_plot(pick_event: PickEvent, mouse_event: MouseEvent, args: Args) \
        -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.plot(...)`.
    """
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
def get_override_group_for_axes_scatter(pick_event: PickEvent, mouse_event: MouseEvent, args: Args) \
        -> OverrideGroup:
    """
    Returns a group of overrides implementing a mouse interaction with graphics created by `plt.scatter(...)`.
    """
    return get_override_group_by_indices(XY(args[1], args[2]), None, pick_event, mouse_event)
