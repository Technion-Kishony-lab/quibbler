from typing import Callable, Optional, NamedTuple, Union, Tuple

import numpy as np
from numpy._typing import NDArray

from numpy.linalg import norm
from numbers import Number

from pyquibbler.quib.graphics.event_handling.utils import get_closest_point_on_line
from pyquibbler.quib.types import PointArray
from pyquibbler.utilities.numpy_original_functions import np_array


class Solution(NamedTuple):
    value: Union[Number, Tuple[Number, ...]]
    point: PointArray
    distance: Number
    tol_value: Union[Number, Tuple[Number, ...]]


def solve_single_point_on_curve(func: Callable,
                                v0: NDArray, v1: NDArray,
                                xy: PointArray, tolerance: Union[Number, PointArray] = 1,
                                max_iter: int = 10,
                                p0: Optional[PointArray] = None
                                ) -> (NDArray, PointArray, NDArray, int):
    """
    Find the variable value for which the curve defined by func is closest to the point xy.

    Parameters
    ----------
    func : Callable
        A function of a single variable. Returns a PointArray.
    v0 : NDArray
        Array of shape (1, ) with the initial guess for the variable value.
    v1 : NDArray
        Array of shape (1, ) with the second guess for the variable value.
    xy : PointArray
        The point for which the curve should be closest to.
    tolerance : Number or PointArray
        The tolerance for the distance between the curve and the point.
    p0 : Optional[PointArray]
        The point on the curve at v0. If None, it is calculated by calling func(v0).
    """

    v0 = v0[0]
    v1 = v1[0]

    if p0 is None:
        p0 = func((v0, ))

    p1 = func((v1, ))

    num_iter = 0
    best_solution = None
    while True:
        dv = v1 - v0
        dpv = p1 - p0
        dpv_norm = norm(dpv)
        tol_v = dv / dpv_norm * tolerance
        distance = norm(p1 - xy)
        if best_solution is None or distance < best_solution.distance:
            best_solution = Solution(v1, p1, distance, tol_v)
        else:
            break

        p_target, slope = get_closest_point_on_line(p0, p1, xy)
        if norm((p1 - p_target) / tolerance) < 1 or num_iter >= max_iter:
            break

        overshoot = dpv_norm / norm(p_target - p0)
        v2 = v0 + dv / overshoot
        num_iter += 1
        p2 = func((v2, ))
        v0, v1 = v1, v2
        p0, p1 = p1, p2

    return np_array([best_solution.value]), best_solution.point, np_array([best_solution.tol_value]), num_iter


def decompose_vector_into_two_components(vw: PointArray, xy: PointArray) -> Tuple[NDArray, bool]:
    """
    Decompose the vector xy into two components, one in the direction of v and one in the direction of w.

    Parameters
    ----------
    vw : PointArray
        The two vectors v and w.
    xy : PointArray
        The vector to decompose.

    Returns
    -------
    Tuple[Number, Number]
        The coefficients c_v and c_w such that xy = c_v * v + c_w * w.
    """
    v, w = vw
    denominator = v[0] * w[1] - v[1] * w[0]
    if abs(denominator) > 1e-10:
        c_v = (w[1] * xy[0] - w[0] * xy[1]) / denominator
        c_w = (v[0] * xy[1] - v[1] * xy[0]) / denominator
        return np_array([c_v, c_w]), True

    # the two vectors are parallel
    # for each vector, calculate the coefficient that minimizes the distance to xy:
    norm_v = v[0] ** 2 + v[1] ** 2
    norm_w = w[0] ** 2 + w[1] ** 2
    if norm_v == 0:
        c_v = 0
    else:
        c_v = (v[0] * xy[0] + v[1] * xy[1]) / norm_v

    if norm_w == 0:
        c_w = 0
    else:
        c_w = (w[0] * xy[0] + w[1] * xy[1]) / norm_w

    if c_v and c_w:
        # if both vectors contribute to the distance, make them contribute equally:
        return np_array([c_v / 2, c_w / 2]), False
    return np_array([c_v, c_w]), False


def solve_single_point_with_two_variables(func: Callable,
                                          v0: NDArray, v1: NDArray,
                                          xy: PointArray, tolerance: Number = 1,
                                          max_iter: Optional[int] = None,
                                          p0: Optional[PointArray] = None,
                                          ) -> (NDArray, PointArray, NDArray, int):
    """
    Find the variable values for which the curve defined by func is closest to the point xy.

    Parameters
    ----------
    func : Callable
        A function of two variables. Returns a PointArray.
    v0 : NDArray
        The initial guess for the two variable values.
    v1 : NDArray
        The second guess for the two variable values.
    xy : PointArray
        The point for which the curve should be closest to.
    tolerance : float
        The tolerance for the distance between the curve and the point.
    p0 : Optional[PointArray]
        The point on the curve at v0, w0. If None, it is calculated by calling func(v0, w0).
    """
    num_iter = 0
    closest = None
    if p0 is None:
        p0 = func(v0)

    while True:
        dv = v1 - v0
        p_ab = np_array([
            func(v0 + dv * [1, 0]),
            func(v0 + dv * [0, 1])
        ])

        dp = p_ab - p0
        dp_norm = norm(dp, axis=1)

        if np.all(dp_norm == 0):
            #  dragging a point that is not movable:
            diff_norm = norm(xy - p0)
            closest = Solution(v1, p0, diff_norm, np.abs(dv) / diff_norm * tolerance)
            break

        # calculate the coefficients c_v and c_w such that p00 + c_v * dp01 + c_w * dp10 == xy
        coefs, is_independent = decompose_vector_into_two_components(dp, xy - p0)
        expected_xy = p0 + coefs @ dp
        if is_independent:
            assert np.allclose(expected_xy, xy, atol=1e-6), f'{expected_xy} != {xy}'

        expected_v = v0 + coefs * dv
        p_at_expected = func(expected_v)

        distance_to_xy = norm(p_at_expected - xy)
        if closest is None or distance_to_xy < closest.distance:
            old_tol_v = closest.tol_value if closest is not None else np.zeros_like(dv)
            # do not warn on division by zero, because it is handled in the next line:
            with np.errstate(divide='ignore', invalid='ignore'):
                tol_v = np.abs(dv) / dp_norm * tolerance
            tol_v[dv == 0] = old_tol_v[dv == 0]
            closest = Solution(expected_v, p_at_expected, distance_to_xy, tol_v)
        else:
            break

        distance_to_expected_xy = norm(p_at_expected - expected_xy)
        if distance_to_expected_xy < tolerance or (max_iter is not None and num_iter >= max_iter):
            break

        c_new, _ = decompose_vector_into_two_components(dp, xy - p_at_expected)
        v2 = expected_v + dv * c_new

        num_iter += 1
        v0 = expected_v
        p0 = p_at_expected
        v1 = v2

    return closest.value, closest.point, closest.tol_value, num_iter
