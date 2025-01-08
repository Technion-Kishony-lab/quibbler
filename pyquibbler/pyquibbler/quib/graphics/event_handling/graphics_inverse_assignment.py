from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from numbers import Number

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, MouseButton

from typing import Any, Union, Optional, List, Tuple

from numpy._typing import NDArray
from numpy.linalg import norm

from pyquibbler.assignment import get_axes_x_y_tolerance, OverrideGroup, \
    AssignmentToQuib, default, get_override_group_for_quib_change, create_assignment
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
from pyquibbler.path import deep_get
from pyquibbler.utilities.numpy_original_functions import np_array

from .affected_args_and_paths import get_quib_and_path_affected_by_event
from .enhance_pick_event import EnhancedPickEventWithFuncArgsKwargs
from .solvers import solve_single_point_on_curve, solve_single_point_with_two_variables
from .utils import get_closest_point_on_line_in_axes, skip_vectorize

from typing import TYPE_CHECKING

from pyquibbler.quib.types import PointArray

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


def _get_overrides_from_changes(quib_and_path: NDArray[QuibAndPath], value: NDArray[Number]):
    xy_quib_changes = skip_vectorize(get_assignment_to_quib_from_quib_and_path)(
        quib_and_path, value)
    xys_overrides = skip_vectorize(get_override_group_for_quib_change)(xy_quib_changes, should_raise=False)
    return xys_overrides


def _get_unique_overrides_and_initial_values(overrides: List[AssignmentToQuib]) -> Tuple[OverrideGroup, List[Number]]:
    """
    find all the unique quib x paths in the overrides
    to assess if override B is the same as A, we apply A and check if B is changing to the same value
    we cannot directly compare the path because the path might look different but point to the same element
    overrides: list of AssignmentToQuib
    """
    unique_overrides = OverrideGroup()
    initial_values = []

    overrides_to_initial_values = {
        override: _get_quib_value_at_path((override.quib, override.assignment.path))
        for override in overrides
    }

    while len(overrides_to_initial_values) > 0:
        # get the first item (not the last) to ensure the order is consistent
        override = next(iter(overrides_to_initial_values))
        initial_value = overrides_to_initial_values.pop(override)
        # remove all the overrides that are the same as the current override
        with OverrideGroup([override]).temporarily_apply():
            new_value = _get_quib_value_at_path((override.quib, override.assignment.path))
            if new_value == initial_value:
                continue
            unique_overrides.append(override)
            initial_values.append(initial_value)
            for other_override, other_initial_value in list(overrides_to_initial_values.items()):
                other_new_value = _get_quib_value_at_path((other_override.quib, other_override.assignment.path))
                if other_initial_value == initial_value and other_new_value == new_value:
                    overrides_to_initial_values.pop(other_override)
    return unique_overrides, initial_values


def _transform_data_with_none_to_pixels(ax: Axes, data: PointArray) -> PointArray:
    data = np.where(data == None, 0, data)  # noqa
    return PointArray(ax.transData.transform(data))


def _get_point_on_line_in_axes(ax: Axes,
                               overrides: OverrideGroup,
                               xy_quib_and_path: PointArray[QuibAndPath],
                               values: List[Number],
                               ) -> PointArray:
    """
    function to use in solve_single_point_on_curve
    """
    for override, value in zip(overrides, values):
        override.assignment.value = value
    with overrides.temporarily_apply():
        xy_data = skip_vectorize(_get_quib_value_at_path)(xy_quib_and_path)
    return _transform_data_with_none_to_pixels(ax, xy_data)


@dataclass
class GetOverrideGroupFromGraphics:
    xy_args: NDArray
    data_index: Union[None, int]
    enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs
    mouse_event: MouseEvent

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

    def _is_dragged_in_x_more_than_y(self) -> bool:
        """
        Return True / False if mouse is dragged mostly in the x / y direction.
        """
        return abs(self.enhanced_pick_event.x - self.mouse_event.x) > \
            abs(self.enhanced_pick_event.y - self.mouse_event.y)

    @property
    def xy_mouse(self) -> PointArray:
        return PointArray([[self.mouse_event.x, self.mouse_event.y]])

    @property
    def ax(self):
        return self.enhanced_pick_event.ax

    @property
    def xys_target_values_pixels(self) -> PointArray:
        return self.xy_mouse + self.enhanced_pick_event.xy_offset

    def _get_target_values_pixels(self, j_ind) -> PointArray:
        xys_target_values_pixels = self.xys_target_values_pixels
        return xys_target_values_pixels[min(j_ind, len(xys_target_values_pixels) - 1)]

    def get_xy_old_and_target_values(self, xys_arg_quib_and_path) -> tuple[PointArray, PointArray]:
        xys_old = skip_vectorize(_get_quib_value_at_path)(xys_arg_quib_and_path)

        transData_inverted = self.ax.transData.inverted()
        xys_target_values = transData_inverted.transform(self.xys_target_values_pixels)
        xys_target_values_typed = skip_vectorize(convert_scalar_value)(xys_old, xys_target_values)

        unchanged = xys_target_values_typed == xys_old
        if np.any(unchanged):
            # if the target value is the same as the old value, we add a pixel to the target value
            # to have some scale for the solver
            xys_target_values_1 = transData_inverted.transform(self.xys_target_values_pixels + 1)
            xys_target_values_typed_1 = skip_vectorize(convert_scalar_value)(xys_old, xys_target_values_1)
            xys_target_values_typed[unchanged] = xys_target_values_typed_1[unchanged]
        return xys_old, xys_target_values_typed

    def _get_overrides_for_single_point_on_curve(
            self, j_ind, xys_arg_quib_and_path, xys_old, unique_source_overrides, unique_source_initial_values):
        value, _, tol_value, _ = solve_single_point_on_curve(
            func=partial(_get_point_on_line_in_axes, self.ax, unique_source_overrides, xys_arg_quib_and_path[j_ind]),
            v0=unique_source_initial_values[0],
            v1=unique_source_overrides[0].assignment.value,
            xy=self._get_target_values_pixels(j_ind),
            tolerance=1,
            max_iter=4,
            p0=_transform_data_with_none_to_pixels(self.ax, xys_old[j_ind]),
        )
        unique_source_overrides[0].assignment = \
            create_assignment(value, unique_source_overrides[0].assignment.path,
                              None if GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val is None
                              else tol_value / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val * 1000)
        return unique_source_overrides

    def _get_overrides_for_single_point_with_two_variables(
            self, j_ind, xys_arg_quib_and_path, xys_old, unique_source_overrides, unique_source_initial_values):
        v1 = np_array([unique_source_overrides[0].assignment.value, unique_source_overrides[1].assignment.value])
        values, solution_point, tol_values, _ = solve_single_point_with_two_variables(
            func=partial(_get_point_on_line_in_axes, self.ax, unique_source_overrides, xys_arg_quib_and_path[j_ind]),
            v0=np_array(unique_source_initial_values),
            v1=v1,
            xy=self._get_target_values_pixels(j_ind),
            tolerance=1,
            max_iter=6,
            p0=_transform_data_with_none_to_pixels(self.ax, xys_old[j_ind]))
        for override, value, tol_value in zip(unique_source_overrides, values, tol_values):
            override.assignment = \
                create_assignment(value, override.assignment.path,
                                  None if GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val is None
                                  else tol_value / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val * 1000)
        return unique_source_overrides

    def get_overrides(self) -> OverrideGroup:
        point_indices = np.reshape(self.enhanced_pick_event.ind, (-1, 1))
        num_points = point_indices.size

        # For x and y, get list of (quib, path) for each affected plot index. None if not a quib
        xys_arg_quib_and_path = skip_vectorize(get_quib_and_path_affected_by_event)(
            [self.xy_args], self.data_index, point_indices)

        if self.enhanced_pick_event.button is MouseButton.RIGHT:
            # Right click. We reset the quib to its default value
            xys_overrides = _get_overrides_from_changes(xys_arg_quib_and_path, default)
            return OverrideGroup([o for o in xys_overrides.flatten() if o is not None])

        if self.mouse_event.x is None or self.mouse_event.y is None:
            # Out of axes
            return OverrideGroup()

        xys_old, xys_target_values = self.get_xy_old_and_target_values(xys_arg_quib_and_path)

        xys_overrides = _get_overrides_from_changes(xys_arg_quib_and_path, xys_target_values)

        xys_source_overrides = skip_vectorize(lambda x: x[0])(xys_overrides)
        xy_order = (0, 1) if self._is_dragged_in_x_more_than_y() else (1, 0)

        overrides = OverrideGroup()

        for j_ind in range(num_points):

            unique_source_overrides, unique_source_initial_values = _get_unique_overrides_and_initial_values(
                [o for o in xys_source_overrides[j_ind, xy_order] if o is not None])

            if len(unique_source_overrides) == 1:
                overrides.extend(self._get_overrides_for_single_point_on_curve(
                    j_ind, xys_arg_quib_and_path, xys_old, unique_source_overrides, unique_source_initial_values))

            elif len(unique_source_overrides) == 2:
                overrides.extend(self._get_overrides_for_single_point_with_two_variables(
                    j_ind, xys_arg_quib_and_path, xys_old, unique_source_overrides, unique_source_initial_values))

        return overrides
