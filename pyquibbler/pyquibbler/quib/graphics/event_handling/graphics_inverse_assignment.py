from __future__ import annotations

from numbers import Number

import numpy as np
from matplotlib.backend_bases import MouseEvent, MouseButton

from typing import Any, Union, Optional

from numpy._typing import NDArray

from pyquibbler.assignment import get_axes_x_y_tolerance, OverrideGroup, \
    AssignmentToQuib, default, get_override_group_for_quib_change
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.path import deep_get
from pyquibbler.utilities.numpy_original_functions import np_array

from .affected_args_and_paths import get_quib_and_path_affected_by_event
from .enhance_pick_event import EnhancedPickEventWithFuncArgsKwargs
from .utils import get_closest_point_on_line_in_axes, get_intersect_between_two_lines_in_axes, skip_vectorize

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .affected_args_and_paths import QuibAndPath


def _get_quib_value_at_path(quib_and_path: Optional[QuibAndPath]) -> Optional[Number]:
    quib, path = quib_and_path
    return deep_get(quib.get_value_valid_at_path(path), path)


def get_assignment_to_quib_from_quib_and_path(quib_and_path: Optional[QuibAndPath],
                                      value: Any = default, tolerance: Any = None,
                                      ) -> Optional[AssignmentToQuib]:
    return AssignmentToQuib.create(*quib_and_path, value, tolerance)


def _calculate_assignment_overshoot(old_val, new_val, assigned_val) -> Optional[float]:
    """
    Returns the factor by which the point moved more/less than expected.
    Return `None` if didn't move.
    """
    return None if new_val == old_val else (assigned_val - old_val) / (new_val - old_val)


def _is_dragged_in_x_more_than_y(enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs, mouse_event: MouseEvent) -> bool:
    """
    Return True / False if mouse is dragged mostly in the x / y direction.
    """
    return abs(enhanced_pick_event.x - mouse_event.x) > abs(enhanced_pick_event.y - mouse_event.y)


def _temp_apply_and_get_new_value(override: OverrideGroup, xy_quib_and_path: NDArray[QuibAndPath]) -> NDArray[Number]:
    """
    Apply the override temporarily and get the new value of the quib
    """
    from pyquibbler import Project
    project = Project.get_or_create()
    override.apply(temporarily=True)
    new_value = skip_vectorize(_get_quib_value_at_path)(xy_quib_and_path)
    project.undo_pending_group(temporarily=True)
    return new_value


def _get_overrides_from_changes(quib_and_path: NDArray[QuibAndPath], value: NDArray[Number]):
    xy_quib_changes = skip_vectorize(get_assignment_to_quib_from_quib_and_path)(
        quib_and_path, value)
    xys_overrides = skip_vectorize(get_override_group_for_quib_change)(xy_quib_changes, should_raise=False)
    return xy_quib_changes, xys_overrides


def get_override_group_by_indices(xy_args: NDArray, data_index: Union[None, int],
                                  enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs, mouse_event: MouseEvent) -> OverrideGroup:
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

    point_indices = np.reshape(enhanced_pick_event.ind, (-1, 1))

    # For x and y, get list of (quib, path) for each affected plot index. None if not a quib
    xys_arg_quib_and_path = skip_vectorize(get_quib_and_path_affected_by_event)([xy_args], data_index, point_indices)

    if enhanced_pick_event.button is MouseButton.RIGHT:
        _, xys_overrides = _get_overrides_from_changes(xys_arg_quib_and_path, default)
        return OverrideGroup([o for o in xys_overrides.flatten() if o is not None])

    if mouse_event.x is None or mouse_event.y is None:
        # out of axes
        return OverrideGroup()

    ax = enhanced_pick_event.ax
    xy_mouse = np_array([[mouse_event.x, mouse_event.y]])
    xys_old = skip_vectorize(_get_quib_value_at_path)(xys_arg_quib_and_path)
    xys_target_values_pixels = xy_mouse + enhanced_pick_event.xy_offset
    transData_inverted = ax.transData.inverted()
    xys_target_values = transData_inverted.transform(xys_target_values_pixels)
    xys_target_values = skip_vectorize(convert_scalar_value)(xys_old, xys_target_values)

    xy_quib_changes, xys_overrides = _get_overrides_from_changes(xys_arg_quib_and_path, xys_target_values)

    xy_tolerance = get_axes_x_y_tolerance(ax)
    xys_sources = skip_vectorize(lambda x: x[0])(xys_overrides)

    for quibs_and_paths, overrides, sources, xy_old, xy_target_values \
            in zip(xys_arg_quib_and_path, xys_overrides, xys_sources, xys_old, xys_target_values):
        xy_order = (0, 1) if _is_dragged_in_x_more_than_y(enhanced_pick_event, mouse_event) else (1, 0)
        for focal_xy in xy_order:
            other_xy = 1 - focal_xy
            if overrides[focal_xy] is None:
                continue
            xy_new = _temp_apply_and_get_new_value(overrides[focal_xy], quibs_and_paths)
            is_other_affected = xy_old[other_xy] != xy_new[other_xy]

            overshoot = _calculate_assignment_overshoot(xy_old[focal_xy], xy_new[focal_xy], xy_target_values[focal_xy])
            if overshoot is not None:
                if is_other_affected and ax is not None:
                    xy_along_line, slope = get_closest_point_on_line_in_axes(
                        ax, xy_old, xy_new, xy_target_values)
                    adjusted_assigned_value = xy_along_line[focal_xy]
                    if adjusted_assigned_value is None:
                        continue
                    adjustment_to_tolerance = slope[focal_xy]
                else:
                    adjusted_assigned_value = xy_target_values[focal_xy]
                    adjustment_to_tolerance = 1
                adjusted_value = xy_old[focal_xy] + (adjusted_assigned_value - xy_old[focal_xy]) * overshoot
                adjusted_tolerance = None if xy_tolerance[focal_xy] is None else xy_tolerance[focal_xy] * adjustment_to_tolerance

                adjusted_change = get_assignment_to_quib_from_quib_and_path(quib_and_path=quibs_and_paths[focal_xy],
                                                                            value=adjusted_value,
                                                                            tolerance=adjusted_tolerance)
                override = get_override_group_for_quib_change(adjusted_change)
                overrides[focal_xy] = override
                if is_other_affected:
                    overrides[other_xy] = None
                    break

    return OverrideGroup([o for o in xys_overrides.flatten() if o is not None])


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
