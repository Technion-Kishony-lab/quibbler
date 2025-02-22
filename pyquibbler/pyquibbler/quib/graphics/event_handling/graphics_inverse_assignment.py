from __future__ import annotations

from dataclasses import dataclass

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
from pyquibbler.utilities.numpy_original_functions import np_array, np_vectorize

from .affected_args_and_paths import get_obj_and_path_affected_by_event
from .enhance_pick_event import EnhancedPickEventWithFuncArgsKwargs
from .solvers import solve_single_point_on_curve, solve_single_point_with_two_variables
from .utils import skip_vectorize, is_quib

from typing import TYPE_CHECKING

from pyquibbler.quib.types import PointArray

if TYPE_CHECKING:
    from .affected_args_and_paths import ObjAndPath


def _get_obj_value_at_path(obj_and_path: Optional[ObjAndPath]) -> Optional[Number]:
    obj, path = obj_and_path
    if is_quib(obj):
        obj = obj.get_value_valid_at_path(path)
    return deep_get(obj, path)


def get_assignment_to_quib_from_obj_and_path(obj_and_path: Optional[ObjAndPath],
                                             value: Any = default, tolerance: Any = None,
                                             ) -> Optional[AssignmentToQuib]:
    obj, path = obj_and_path
    if is_quib(obj):
        return AssignmentToQuib.create(obj, path, value, tolerance)
    return None


def _calculate_assignment_overshoot(old_val, new_val, assigned_val) -> Optional[float]:
    """
    Returns the factor by which the point moved more/less than expected.
    Return `None` if didn't move.
    """
    return None if new_val == old_val else (assigned_val - old_val) / (new_val - old_val)


def _get_overrides_from_changes(quib_and_path: NDArray[ObjAndPath], value: NDArray[Number]):
    xy_quib_changes = skip_vectorize(get_assignment_to_quib_from_obj_and_path)(
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
        lambda o: _get_obj_value_at_path((o.quib, o.assignment.path)))(overrides)

    unique_overrides_to_intial_values = {}

    for i, override in enumerate(overrides.flat):
        if override is None:
            continue
        if overrides_unique_num.flat[i] != -1:
            continue
        initial_value = initial_values.flat[i]
        # find all the overrides that are the same as the current override
        with OverrideGroup([override]).temporarily_apply():
            new_value = _get_obj_value_at_path((override.quib, override.assignment.path))
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
                other_new_value = _get_obj_value_at_path((other_override.quib, other_override.assignment.path))
                if other_initial_value == initial_value and other_new_value == new_value:
                    overrides_unique_num.flat[j] = current_num
    return unique_overrides_to_intial_values, overrides_unique_num


@dataclass
class TargetFunc:
    ax: Axes
    overrides: OverrideGroup
    initial_values: NDArray[Number]
    xys_obj_and_path: PointArray[ObjAndPath]
    xys_old: PointArray[Number]

    @property
    def num_values(self) -> int:
        return len(self.overrides)

    def get_override_values(self) -> NDArray[Number]:
        return np_array([o.assignment.value for o in self.overrides])

    def _transform_data_with_none_to_pixels(self, data: PointArray) -> PointArray:
        data = np.where(data == None, 0, data)  # noqa
        return PointArray(self.ax.transData.transform(data))

    def assign_values(self, values: List[Number]):
        for override, value in zip(self.overrides, values):
            override.assignment.value = value

    def _get_xy_data(self, values: Optional[List[Number]]) -> PointArray:
        if values is None:
            return self.xys_old
        self.assign_values(values)
        with self.overrides.temporarily_apply():
            return skip_vectorize(_get_obj_value_at_path)(self.xys_obj_and_path)

    def _get_xy_pixel_data(self, values: Optional[List[Number]]) -> PointArray:
        return self._transform_data_with_none_to_pixels(self._get_xy_data(values))

    def get_result(self, values: Optional[List[Number]]) -> PointArray:
        return NotImplemented


class SinglePointTargetFunc(TargetFunc):
    def get_result(self, values: List[Number]) -> PointArray:
        return self._get_xy_pixel_data(values)


@dataclass
class SegmentPointTargetFunc(TargetFunc):
    segment_fraction: float

    def get_result(self, values: List[Number]) -> PointArray:
        xy_data = self._get_xy_pixel_data(values)
        return (1 - self.segment_fraction) * xy_data[0] + self.segment_fraction * xy_data[1]


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

    xys_obj_and_path: NDArray[ObjAndPath] = None
    xys_old: NDArray[Number] = None
    unique_source_overrides_and_initial_values: NDArray = None
    xys_unique_source_ids: NDArray[int] = None

    """
    Get overrides for a mouse event for an artist created by a ploting command (plot, scatter, axvline, etc).

    `xy_args` is a numpy array of shape (2,).
    It contains the x and y arguments of the ploting command.

    `data_index` the index of the artist. for multiuple lines created by a plot command of 2D data,

    `data_index=None`: denotes artist produced by plt.scatter (where the x and y arguments are treated as flatten)

    The function treats these possibilities:

    1. x, y are not quibs, or are quibs that cannot be inverted:
       Dragging is disabled

    2. only x or only y are invertible quibs:
       Horizontal or vertical dragging. Invert x/y of the mouse to the quib.

    3. both x and y quibs but their inversion trace to the same source:
       We are draging on a curve. Invert to the point on the curve closest to the mouse.

    4. both x and y can be inverted to different quibs:
       Solve for the x,y point closest to the mouse.

    5. segment:
         If the segment is movable, we solve for the segment point closest to the mouse.
            If the segment is not movable, we solve for the segment points independently.
    """

    # Numenclature:
    # xys_ : numpy array of shape (num_points, 2).
    # xy_ : numpy array of shape (2,).
    # obj : can be either a quib or non-quib argument of the ploting function.

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

    @property
    def point_indices(self) -> NDArray[int]:
        return np.reshape(self.enhanced_pick_event.ind, (-1, 1))

    @property
    def num_points(self) -> int:
        return self.point_indices.size

    def _get_target_values_pixels(self, j_ind) -> PointArray:
        xys_target_values_pixels = self.xys_target_values_pixels
        return xys_target_values_pixels[min(j_ind, len(xys_target_values_pixels) - 1)]

    def _get_source_ids(self, j_ind: Optional[int]) -> NDArray[int]:
        """Get the source ids of a given point, or the source ids of the segment"""
        ids = self.xys_unique_source_ids[j_ind].flatten()
        ids = ids[ids != -1]
        return np.unique(ids)

    def _get_target_segment_held_point(self) -> PointArray:
        return self.xy_mouse[0] + self.enhanced_pick_event.mouse_to_segment

    def get_xy_old_and_target_values(self, xys_obj_and_path) -> tuple[PointArray, PointArray]:
        xys_old = skip_vectorize(_get_obj_value_at_path)(xys_obj_and_path)
        is_quib_vec = np_vectorize(lambda o_and_p: o_and_p is not None and is_quib(o_and_p[0]))(xys_obj_and_path)
        transData_inverted = self.ax.transData.inverted()
        xys_target_values = transData_inverted.transform(self.xys_target_values_pixels)
        xys_target_values_typed = skip_vectorize(convert_scalar_value)(xys_old, xys_target_values)

        unchanged = (xys_target_values_typed == xys_old) & is_quib_vec
        if np.any(unchanged):
            # if the target value is the same as the old value, we add a pixel to the target value
            # to have some scale for the solver
            xys_target_values_1 = transData_inverted.transform(self.xys_target_values_pixels + 1)
            xys_target_values_typed_1 = skip_vectorize(convert_scalar_value)(xys_old, xys_target_values_1)
            xys_target_values_typed[unchanged] = xys_target_values_typed_1[unchanged]
        return xys_old, xys_target_values_typed

    def _call_geometric_solver(self, target_func: TargetFunc, xy, with_tolerance=True) -> OverrideGroup:
        solver = self.nun_args_to_solvers.get(target_func.num_values)
        if solver is None:
            return OverrideGroup()
        values, _, tol_values, _ = solver(func=target_func.get_result, v0=target_func.initial_values,  # noqa
                                          v1=target_func.get_override_values(),
                                          xy=xy, tolerance=1, max_iter=6,
                                          p0=target_func.get_result(None))

        overrides = OverrideGroup()
        for override, value, tol_value in zip(target_func.overrides, values, tol_values):
            override.assignment = \
                create_assignment(value, override.assignment.path,
                                  None if GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val is None or not with_tolerance
                                  else tol_value / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val * 1000)
            overrides.append(override)
        return overrides

    def _get_overrides_for_point(self, j_ind: int, with_tolerance=True) -> OverrideGroup:
        source_ids = self._get_source_ids(j_ind)
        if len(source_ids) == 0:
            return OverrideGroup()

        target_func = SinglePointTargetFunc(
            ax=self.ax, overrides=OverrideGroup(self.unique_source_overrides_and_initial_values[source_ids, 0]),
            initial_values=self.unique_source_overrides_and_initial_values[source_ids, 1],
            xys_obj_and_path=self.xys_obj_and_path[j_ind], xys_old=self.xys_old[j_ind])
        xy = self._get_target_values_pixels(j_ind)

        return self._call_geometric_solver(target_func, xy, with_tolerance)

    def _get_overrides_for_segment(self):
        num_unique_sources = len(self.unique_source_overrides_and_initial_values)
        source_ids0, source_ids1 = self._get_source_ids(0), self._get_source_ids(1)
        num_overlaping_sources = len(set(source_ids0) & set(source_ids1))
        num_points_with_sources = (len(source_ids0) > 0) + (len(source_ids1) > 0)
        if (num_overlaping_sources > 0 or num_points_with_sources == 1) and 1 <= num_unique_sources <= 2:
            # These are the conditions in which we solve for getting the mouse-held segment point close to the mouse
            # rather than moving each of the segment points independently
            segment_fraction = self.enhanced_pick_event.segment_fraction
            target_func = SegmentPointTargetFunc(
                ax=self.ax, overrides=OverrideGroup(self.unique_source_overrides_and_initial_values[:, 0]),
                initial_values=self.unique_source_overrides_and_initial_values[:, 1],
                xys_obj_and_path=self.xys_obj_and_path, xys_old=self.xys_old, segment_fraction=segment_fraction)

            return self._call_geometric_solver(target_func, self._get_target_segment_held_point(), with_tolerance=True)

        # We move each of the segment points independently
        overrides = OverrideGroup()
        for j_ind in range(self.num_points):
            # suppress tolerance so that the segment points are moved together
            overrides.extend(self._get_overrides_for_point(j_ind, with_tolerance=False))
        return overrides

    def _get_overrides_for_right_click(self, xys_obj_and_path):
        """ Right click. We reset the quib to its default value """
        xys_overrides = _get_overrides_from_changes(xys_obj_and_path, default)
        return OverrideGroup([o for o in xys_overrides.flatten() if o is not None])

    def get_overrides(self) -> OverrideGroup:

        self.xys_obj_and_path = skip_vectorize(get_obj_and_path_affected_by_event)(
            [self.xy_args], self.data_index, self.point_indices)

        if self.enhanced_pick_event.button is MouseButton.RIGHT:
            return self._get_overrides_for_right_click(self.xys_obj_and_path)

        if self.mouse_event.x is None or self.mouse_event.y is None:
            # Out of axes
            return OverrideGroup()

        self.xys_old, self.xys_target_values = self.get_xy_old_and_target_values(self.xys_obj_and_path)

        # to allow plot with str values (see test_drag_with_non_numeric_on_one_axis):
        is_str = np.vectorize(lambda x: isinstance(x, str))(self.xys_old)
        self.xys_obj_and_path[is_str] = None
        self.xys_target_values[is_str] = None
        self.xys_old[is_str] = None

        xys_overrides = _get_overrides_from_changes(self.xys_obj_and_path, self.xys_target_values)

        xys_source_overrides = skip_vectorize(lambda x: x[0])(xys_overrides)
        xy_order = (0, 1) if self._is_dragged_in_x_more_than_y() else (1, 0)
        unique_source_overrides_to_initial_values, self.xys_unique_source_ids = \
            _get_unique_overrides_and_initial_values(xys_source_overrides[:, xy_order])
        self.unique_source_overrides_and_initial_values = \
            np_array(list(unique_source_overrides_to_initial_values.items()), dtype=object)

        if self.num_points == 2:
            return self._get_overrides_for_segment()

        return self._get_overrides_for_point(0)
