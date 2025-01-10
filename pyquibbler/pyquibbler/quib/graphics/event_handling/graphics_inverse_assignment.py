from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from numbers import Number

import numpy as np
from matplotlib.axes import Axes
from matplotlib.backend_bases import MouseEvent, MouseButton

from typing import Any, Union, Optional, List, Tuple, Dict

from numpy._typing import NDArray

from pyquibbler.assignment import OverrideGroup, \
    AssignmentToQuib, default, get_override_group_for_quib_change, create_assignment
from pyquibbler.assignment.utils import convert_scalar_value
from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
from pyquibbler.path import deep_get
from pyquibbler.utilities.numpy_original_functions import np_array

from .affected_args_and_paths import get_quib_and_path_affected_by_event
from .enhance_pick_event import EnhancedPickEventWithFuncArgsKwargs
from .solvers import solve_single_point_on_curve, solve_single_point_with_two_variables
from .utils import skip_vectorize

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


def _get_unique_overrides_and_initial_values(overrides: NDArray[Optional[AssignmentToQuib]]
                                             ) -> Tuple[Dict[AssignmentToQuib, Number], NDArray[int]]:
    """
    find all the unique quib x paths in the overrides
    to assess if override B is the same as A, we apply A and check if B is changing to the same value
    we cannot directly compare the path because the path might look different but point to the same element
    overrides: list of AssignmentToQuib
    """
    # initiate an object array of size of overrides with all values 'None'
    overrides_unique_num = np.zeros_like(overrides, dtype=int) - 1

    initial_values = skip_vectorize(
        lambda o: _get_quib_value_at_path((o.quib, o.assignment.path)))(overrides)

    unique_overrides_to_intial_values = {}

    for i, override in enumerate(overrides.flat):
        if override is None:
            continue
        if overrides_unique_num.flat[i] != -1:
            continue
        initial_value = initial_values.flat[i]
        # find all the overrides that are the same as the current override
        with OverrideGroup([override]).temporarily_apply():
            new_value = _get_quib_value_at_path((override.quib, override.assignment.path))
            if new_value == initial_value:
                # this override is effectless. we skip it
                continue
            current_num = len(unique_overrides_to_intial_values)
            overrides_unique_num.flat[i] = current_num
            unique_overrides_to_intial_values[override] = initial_value
            for j in range(i + 1, overrides.size):
                other_override = overrides.flat[j]
                if other_override is None:
                    continue
                other_initial_value = initial_values.flat[j]
                other_new_value = _get_quib_value_at_path((other_override.quib, other_override.assignment.path))
                if other_initial_value == initial_value and other_new_value == new_value:
                    overrides_unique_num.flat[j] = current_num
    return unique_overrides_to_intial_values, overrides_unique_num


def _transform_data_with_none_to_pixels(ax: Axes, data: PointArray) -> PointArray:
    data = np.where(data == None, 0, data)  # noqa
    return PointArray(ax.transData.transform(data))


def _get_axes_point_from_quib_and_paths(ax: Axes,
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


def _get_axes_segment_point_from_quib_and_paths(ax: Axes,
                                                overrides: OverrideGroup,
                                                xy_quib_and_path: PointArray[QuibAndPath],
                                                values: List[PointArray],
                                                segment_fraction: float,
                                                ) -> PointArray:
    xy_data = _get_axes_point_from_quib_and_paths(ax, overrides, xy_quib_and_path, values)
    return (1 - segment_fraction) * xy_data[0] + segment_fraction * xy_data[1]


@dataclass
class GetOverrideGroupFromGraphics:
    xy_args: NDArray
    data_index: Union[None, int]
    enhanced_pick_event: EnhancedPickEventWithFuncArgsKwargs
    mouse_event: MouseEvent

    nun_args_to_solvers = {
        1: solve_single_point_on_curve,
        2: solve_single_point_with_two_variables,
    }

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

    def _get_target_segment_held_point(self) -> PointArray:
        return self.xy_mouse[0] + self.enhanced_pick_event.mouse_to_segment

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

    def _call_geometric_solver(self, j_ind,
                               xys_arg_quib_and_path, xys_old, unique_source_overrides, unique_source_initial_values):

        solver = self.nun_args_to_solvers.get(len(unique_source_overrides))
        if solver is None:
            return

        if j_ind is None:
            # segment
            segment_fraction = self.enhanced_pick_event.segment_fraction
            func = partial(_get_axes_segment_point_from_quib_and_paths, self.ax, unique_source_overrides,
                           xys_arg_quib_and_path,
                           segment_fraction=segment_fraction)
            p0 = _transform_data_with_none_to_pixels(self.ax, xys_old)
            p0 = (1 - segment_fraction) * p0[0] + segment_fraction * p0[1]
            xy = self._get_target_segment_held_point()
        else:
            # point
            func = partial(_get_axes_point_from_quib_and_paths, self.ax, unique_source_overrides,
                           xys_arg_quib_and_path[j_ind])
            p0 = _transform_data_with_none_to_pixels(self.ax, xys_old[j_ind])
            xy = self._get_target_values_pixels(j_ind)

        return solver(
            func=func,
            v0=np_array(unique_source_initial_values),
            v1=np_array([o.assignment.value for o in unique_source_overrides]),
            xy=xy,
            tolerance=1,
            max_iter=6,
            p0=p0)

    def _translate_geometric_solution_to_overrides(self, values, tol_values, unique_source_overrides):
        overrides = OverrideGroup()
        for override, value, tol_value in zip(unique_source_overrides, values, tol_values):
            override.assignment = \
                create_assignment(value, override.assignment.path,
                                  None if GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val is None
                                  else tol_value / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val * 1000)
            overrides.append(override)
        return overrides

    def _call_geometric_solver_and_get_overrides(self, j_ind, source_nums, xys_arg_quib_and_path, xys_old,
                                                 unique_source_overrides_and_initial_values):
        unique_source_overrides = OverrideGroup(unique_source_overrides_and_initial_values[source_nums, 0])
        unique_source_initial_values = unique_source_overrides_and_initial_values[source_nums, 1]
        values, _, tol_values, _ = self._call_geometric_solver(
            j_ind, xys_arg_quib_and_path, xys_old, unique_source_overrides, unique_source_initial_values)
        return self._translate_geometric_solution_to_overrides(values, tol_values, unique_source_overrides)

    @property
    def point_indices(self) -> NDArray[int]:
        return np.reshape(self.enhanced_pick_event.ind, (-1, 1))

    @property
    def num_points(self) -> int:
        return self.point_indices.size

    def get_overrides(self) -> OverrideGroup:
        # For x and y, get list of (quib, path) for each affected plot index. None if not a quib
        xys_arg_quib_and_path = skip_vectorize(get_quib_and_path_affected_by_event)(
            [self.xy_args], self.data_index, self.point_indices)

        if self.enhanced_pick_event.button is MouseButton.RIGHT:
            # Right click. We reset the quib to its default value
            xys_overrides = _get_overrides_from_changes(xys_arg_quib_and_path, default)
            return OverrideGroup([o for o in xys_overrides.flatten() if o is not None])

        if self.mouse_event.x is None or self.mouse_event.y is None and False:
            # Out of axes
            return OverrideGroup()

        xys_old, xys_target_values = self.get_xy_old_and_target_values(xys_arg_quib_and_path)

        xys_overrides = _get_overrides_from_changes(xys_arg_quib_and_path, xys_target_values)

        xys_source_overrides = skip_vectorize(lambda x: x[0])(xys_overrides)
        xy_order = (0, 1) if self._is_dragged_in_x_more_than_y() else (1, 0)
        unique_source_overrides_to_initial_values, xys_unique_source_nums = \
            _get_unique_overrides_and_initial_values(xys_source_overrides[:, xy_order])
        unique_source_overrides_and_initial_values = \
            np_array(list(unique_source_overrides_to_initial_values.items()), dtype=object)
        sum_unique_sources = len(unique_source_overrides_to_initial_values)

        # for each point, get the unique source nums:
        unique_source_nums = []
        for j_ind in range(self.num_points):
            unique_source_nums.append(
                np.unique([num for num in xys_unique_source_nums[j_ind] if num != -1]))

        if self.enhanced_pick_event.is_segment and self.data_index is not None:
            sum_overlaping_source_nums = len(set(unique_source_nums[0]) & set(unique_source_nums[1]))
            num_points_with_sources = sum(1 for nums in unique_source_nums if len(nums) > 0)
            if (sum_overlaping_source_nums > 0 or num_points_with_sources == 1) and 1 <= sum_unique_sources <= 2:
                # These are the conditions in which we solve for getting the mouse-held segment point close to the mouse
                # rather than moving each of the segment points independently
                return self._call_geometric_solver_and_get_overrides(
                    None, np.arange(sum_unique_sources),
                    xys_arg_quib_and_path, xys_old, unique_source_overrides_and_initial_values)

        overrides = OverrideGroup()
        for j_ind in range(self.num_points):
            source_nums = unique_source_nums[j_ind]
            if len(source_nums) == 0:
                continue
            overrides.extend(self._call_geometric_solver_and_get_overrides(
                j_ind, source_nums,
                xys_arg_quib_and_path, xys_old, unique_source_overrides_and_initial_values))
        return overrides
