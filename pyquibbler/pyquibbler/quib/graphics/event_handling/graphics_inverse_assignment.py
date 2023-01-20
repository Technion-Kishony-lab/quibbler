from __future__ import annotations

from numbers import Number

from matplotlib.backend_bases import PickEvent, MouseEvent, MouseButton

from typing import Any, Union, Optional

from pyquibbler.quib.types import XY, PointXY

from pyquibbler.assignment import get_axes_x_y_tolerance, create_assignment, OverrideGroup, \
    get_override_group_for_quib_changes, AssignmentToQuib, default, get_override_group_for_quib_change
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.path import deep_get
from pyquibbler.utilities.numpy_original_functions import np_array

from .affected_args_and_paths import get_quibs_and_paths_affected_by_event
from .pick_handler import PickHandler
from .utils import get_closest_point_on_line_in_axes, get_intersect_between_two_lines_in_axes

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .affected_args_and_paths import QuibAndPath


def _get_quib_value_at_path(quib_and_path: Optional[QuibAndPath]) -> Optional[Number]:
    if quib_and_path is None:
        return None

    quib, path = quib_and_path
    return deep_get(quib.get_value_valid_at_path(path), path)


def get_assignment_from_quib_and_path(quib_and_path: Optional[QuibAndPath],
                                      value: Any = default, tolerance: Any = None,
                                      ) -> Optional[AssignmentToQuib]:
    """
    Get assignments of mouse coordinate (x or y) to corresponding arg
    """
    if quib_and_path is None or value is None:
        return None
    quib, path = quib_and_path
    return AssignmentToQuib(quib, create_assignment(value, path, tolerance))


def _calculate_assignment_overshoot(old_val, new_val, assigned_val) -> Optional[float]:
    """
    Returns the factor by which the point moved more/less than expected.
    Return `None` if didn't move.
    """
    return None if new_val == old_val else (assigned_val - old_val) / (new_val - old_val)


def _is_dragged_in_x_more_than_y(pick_event: PickEvent, mouse_event: MouseEvent) -> bool:
    """
    Return True / False if mouse is dragged mostly in the x / y direction.
    """
    return abs(pick_event.x - mouse_event.x) > abs(pick_event.y - mouse_event.y)


def get_override_group_by_indices(xy_args: XY, data_index: Union[None, int],
                                  pick_handler: PickHandler, mouse_event: MouseEvent) -> OverrideGroup:
    """
    Get overrides for a mouse event for an artist created by a plt.plot command in correspondence with the
    `data_index` column of the given data arguments xy_args.x, xy_args.y.

    `data_index=None`: denotes artist produced by plt.scatter (where the x and y arguments are treated as flatten)

    the key here is to account for cases where dragging could be restricted to a curve, in which case we want to choose
    the point along the curve closest to the mouse.

    The function treats these possibilities:

    1. x, y are not quibs, or are quibns that cannot be inverted:
        dragging is disabled

    2. only x or only y are invertible quibs:
        if x is a quib, assign mouse-x to it (if inversion is possible). (same for y)

    3. both x and y quibs and the inversion of one affects the other.
        get the "drag-line" by assigning on the axis with larger mouse movement, and invert to the point
        on that line which is closest to the mouse.

    4. both x and y can be inverted without affecting each other.
        return the two inversions.

    We also correct for overshoot assignment due to binary operators. See test_drag_same_arg_binary_operator
    """

    from pyquibbler import Project
    project = Project.get_or_create()
    pick_event = pick_handler.pick_event
    point_indices = pick_event.ind
    ax = pick_event.artist.axes

    # For x and y, get list of (quib, path) for each affected plot index. None if not a quib
    xy_quibs_and_paths = XY.from_func(get_quibs_and_paths_affected_by_event, xy_args, data_index, point_indices)

    if pick_event.mouseevent.button is MouseButton.RIGHT:
        changes = [get_assignment_from_quib_and_path(quib_and_path, default)
                   for quib_and_path in xy_quibs_and_paths.x + xy_quibs_and_paths.y if quib_and_path is not None]
        return get_override_group_for_quib_changes(changes)

    all_overrides = OverrideGroup()
    if mouse_event.x is None or mouse_event.y is None:
        # out of axes
        return all_overrides

    transData_inverted = ax.transData.inverted()

    xy_mouse = np_array([mouse_event.x, mouse_event.y])
    xydata_mouse = PointXY(*transData_inverted.transform(xy_mouse))

    tolerance = get_axes_x_y_tolerance(ax)
    xy_order = (0, 1) if _is_dragged_in_x_more_than_y(pick_event, mouse_event) else (1, 0)

    moved_ok = [False] * len(point_indices)
    for xy_quib_and_path, xy_offset in [(XY(quib_and_path_x, quib_and_path_y), dxy)
                                        for quib_and_path_x, quib_and_path_y, dxy
                                        in zip(xy_quibs_and_paths.x, xy_quibs_and_paths.y, pick_event.xy_offset)]:
        # We go over each index (vertex) of the plot, and translate the x and y assignment to it into overrides
        adjusted_xy_mouse = xy_mouse + xy_offset
        adjusted_xydata_mouse = PointXY(*transData_inverted.transform(adjusted_xy_mouse))

        xy_old = PointXY.from_func(_get_quib_value_at_path, xy_quib_and_path)

        xy_assigned_value = PointXY.from_func(convert_scalar_value, xy_old, adjusted_xydata_mouse)
        xy_change = XY.from_func(get_assignment_from_quib_and_path, xy_quib_and_path, xy_assigned_value)

        overrides = OverrideGroup()

        is_changed = [False, False]
        for focal_xy in xy_order:
            other_xy = 1 - focal_xy

            if xy_quib_and_path[focal_xy] is None:
                continue

            override = get_override_group_for_quib_change(xy_change[focal_xy], should_raise=False)
            if override is None:
                continue

            # temporarily apply change and check the new position of the point at both x and y:
            override.apply(temporarily=True)
            xy_new = PointXY.from_func(_get_quib_value_at_path, xy_quib_and_path)
            project.undo_pending_group(temporarily=True)

            is_other_affected = xy_old[other_xy] != xy_new[other_xy]

            overshoot = _calculate_assignment_overshoot(xy_old[focal_xy], xy_new[focal_xy], xy_assigned_value[focal_xy])

            if overshoot is not None:
                # the quib we assigned to did actually change.
                if is_other_affected and ax is not None:  # ax can be None in testing
                    # The other axis also changed. x and y are dependent. they change along a "drag-line".
                    if pick_event.is_segment:
                        # Find the intersection of the drag-line with the dragged segment.
                        xy_along_line, slope = get_intersect_between_two_lines_in_axes(
                            ax, xy_old, xy_new, xy_assigned_value, xydata_mouse)
                    else:
                        # Find the point on the drag-line which is closest to the mouse position.
                        xy_along_line, slope = get_closest_point_on_line_in_axes(
                            ax, xy_old, xy_new, xy_assigned_value)
                    adjusted_assigned_value = xy_along_line[focal_xy]
                    if adjusted_assigned_value is None:
                        continue  # when we move a segment and the lines are parallel
                    adjustment_to_tolerance = slope[focal_xy]
                else:
                    # we are only dragging in one axis
                    adjusted_assigned_value = xy_assigned_value[focal_xy]
                    adjustment_to_tolerance = 1

                adjusted_change = get_assignment_from_quib_and_path(
                    quib_and_path=xy_quib_and_path[focal_xy],
                    value=xy_old[focal_xy] + (adjusted_assigned_value - xy_old[focal_xy]) * overshoot,
                    tolerance=None if tolerance[focal_xy] is None else tolerance[focal_xy] * adjustment_to_tolerance)
                override = get_override_group_for_quib_change(adjusted_change, should_raise=False)
                if override is None:
                    continue

            overrides.extend(override)
            is_changed[focal_xy] = True
            if is_other_affected:
                # x-y values are dependent. No need to assign to other
                is_changed[other_xy] = True
                break

        if pick_event.is_segment and not any(is_changed):
            return OverrideGroup()

        all_overrides.extend(overrides)
    return all_overrides


# Possible code for improving assignment results using an iterative numeric solution (might be too slow in practice)
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
