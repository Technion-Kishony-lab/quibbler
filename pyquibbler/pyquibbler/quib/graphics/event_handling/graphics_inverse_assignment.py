from __future__ import annotations

import numpy as np

from functools import partial

from matplotlib.axes import Axes
from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton

from typing import Any, List, Tuple, Union, Optional

from pyquibbler.quib.types import XY, PointXY

from pyquibbler.assignment import get_axes_x_y_tolerance, create_assignment, OverrideGroup, \
    get_override_group_for_quib_changes, AssignmentToQuib, Assignment, default, get_override_group_for_quib_change
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.path import PathComponent, Path, deep_get

from .utils import get_closest_point_on_line_in_axes

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


def _get_override_group_for_quib_change_or_none(quib_change: Optional[AssignmentToQuib]) -> Optional[OverrideGroup]:
    return None if quib_change is None else get_override_group_for_quib_change(quib_change, should_raise=False)


def _get_xy_current_point_from_xy_change(xy_change: XY):
    return PointXY.from_func(lambda xy: xy.get_value_at_path(), xy_change)


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
                if len(shape) == 0:
                    path = []
                else:
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


def _calculate_assignment_overshoot(old_val, new_val, assigned_val):
    if assigned_val == old_val or new_val == old_val:
        return 1
    else:
        return (new_val - old_val) / (assigned_val - old_val)


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
        get the drag-line by assigning on the axis with larger mouse movement, and invert to the closest point

    6. both x and y can be inverted without affecting each other.
        return the two inversions.

    We also correct for overshoot assignment due to binary operators. See test_drag_same_arg_binary_operator
    """

    point_indices = pick_event.ind
    ax = pick_event.artist.axes
    quibs_and_paths = XY.from_func(get_quibs_and_paths_affected_by_event, xy_args, data_index, point_indices)

    if pick_event.mouseevent.button is MouseButton.RIGHT:
        changes = XY.from_func(get_plot_arg_assignments_for_event, quibs_and_paths, default)
        changes = [change for change in changes.x + changes.y if change is not None]
        return get_override_group_for_quib_changes(changes)

    all_overrides = OverrideGroup()
    xy_mouse = PointXY(mouse_event.xdata, mouse_event.ydata)
    if xy_mouse.x is None or xy_mouse.y is None:
        # out of axes
        return all_overrides

    tolerance = get_axes_x_y_tolerance(ax)
    if not isinstance(ax, Axes):
        # for testing
        changes = XY.from_func(get_plot_arg_assignments_for_event, quibs_and_paths, xy_mouse, tolerance)
        changes = [change for change in changes.x + changes.y if change is not None]
        return get_override_group_for_quib_changes(changes)

    from pyquibbler import Project
    for quib_and_path, adjust_xy in [(XY(quib_and_path_x, quib_and_path_y), PointXY(dxy[0], dxy[1]))
                                     for quib_and_path_x, quib_and_path_y, dxy
                                     in zip(quibs_and_paths.x, quibs_and_paths.y, pick_event.dxy)]:
        adjusted_xy_mouse = xy_mouse + adjust_xy
        overrides = OverrideGroup()
        if quib_and_path.x is None and quib_and_path.y is None:
            # both x and y are not quibs
            continue
        # TODO: need to unify the two treatments below, for either x or y dragging, and for both x and y dragging.
        elif quib_and_path.is_xor():
            # either only x is a quib or only y is a quib
            focal_xy = 1 if quib_and_path[0] is None else 0
            focal_quib_and_path = quib_and_path[focal_xy]
            focal_change = get_assignment_from_quib_and_path(focal_quib_and_path, adjusted_xy_mouse[focal_xy])
            focal_override = _get_override_group_for_quib_change_or_none(focal_change)
            x_or_y_old = focal_change.get_value_at_path()
            x_or_y_assigned_value = focal_change.assignment.value
            focal_override.apply(temporarily=True)
            x_or_y_new = focal_change.get_value_at_path()
            Project.get_or_create().undo_pending_group(temporarily=True)
            overshoot = _calculate_assignment_overshoot(
                old_val=x_or_y_old,
                new_val=x_or_y_new,
                assigned_val=x_or_y_assigned_value)
            adjusted_change = get_assignment_from_quib_and_path(
                quib_and_path=focal_quib_and_path,
                value=x_or_y_old + (x_or_y_assigned_value - x_or_y_old) / overshoot,
                tolerance=tolerance[focal_xy])
            focal_override = _get_override_group_for_quib_change_or_none(adjusted_change)
            overrides = focal_override or overrides
        else:
            # both x and y are quibs:
            xy_change = XY.from_func(get_assignment_from_quib_and_path, quib_and_path, adjusted_xy_mouse)
            xy_old = _get_xy_current_point_from_xy_change(xy_change)
            xy_assigned_value = PointXY.from_func(lambda xy: xy.assignment.value, xy_change)

            is_mouse_dx_larger_than_dy = \
                np.diff(np.abs(ax.transData.transform(adjusted_xy_mouse) - ax.transData.transform(xy_old))) < 0
            xy_order = (0, 1) if is_mouse_dx_larger_than_dy else (1, 0)  # start with the larger mouse move
            for focal_xy in xy_order:
                other_xy = 1 - focal_xy
                focal_override = _get_override_group_for_quib_change_or_none(xy_change[focal_xy])
                if focal_override is None:
                    continue
                focal_override.apply(temporarily=True)
                xy_new = _get_xy_current_point_from_xy_change(xy_change)
                Project.get_or_create().undo_pending_group(temporarily=True)
                overshoot = _calculate_assignment_overshoot(
                    old_val=xy_old[focal_xy],
                    new_val=xy_new[focal_xy],
                    assigned_val=xy_assigned_value[focal_xy])
                xy_closest, slope = get_closest_point_on_line_in_axes(ax, xy_old, xy_new, xy_assigned_value)
                adjusted_change = get_assignment_from_quib_and_path(
                    quib_and_path=quib_and_path[focal_xy],
                    value=xy_old[focal_xy] + (xy_closest[focal_xy] - xy_old[focal_xy]) / overshoot,
                    tolerance=tolerance[focal_xy] * slope[focal_xy])
                along_line_override = _get_override_group_for_quib_change_or_none(adjusted_change)
                if along_line_override is None:
                    continue

                # Improve results using an iterative numeric solution (too slow in practice)
                # See test_drag_same_arg_binary_operator_non_linear
                #
                # from .utils import get_sqr_distance_in_axes
                # def _distance_to_mouse(assigned_values):
                #     along_line_override.quib_changes[0].assignment.value = assigned_values[0]
                #     along_line_override.apply(temporarily=True)
                #     xy_new = _get_xy_current_point_from_xy_change(xy_change)
                #     Project.get_or_create().silently_undo_pending_group()
                #     return get_sqr_distance_in_axes(ax, xy_new, xy_assigned_value)
                #
                # from scipy.optimize import fmin
                # assigned_value = fmin(_distance_to_mouse, [along_line_override.quib_changes[0].assignment.value],
                #                       xtol=1e10, ftol=1)

                overrides.extend(along_line_override)

                if xy_old[other_xy] != xy_new[other_xy]:
                    # x-y values are dependent
                    break
        all_overrides.extend(overrides)
    return all_overrides
