from typing import Callable, Optional, NamedTuple, Union

from numpy.linalg import norm
from parso.python.tree import Number

from pyquibbler.quib.graphics.event_handling.utils import get_closest_point_on_line
from pyquibbler.quib.types import PointArray


class Solution(NamedTuple):
    value: float
    point: PointArray
    distance: float
    tol_value: float


def solve_single_point_on_curve(func: Callable,
                                v0: Number, v1: Number,
                                xy: PointArray, tolerance: Union[Number, PointArray] = 1,
                                max_iter: int = 10,
                                p0: Optional[PointArray] = None, p1: Optional[PointArray] = None
                                ) -> (float, PointArray, int):
    """
    Find the variable value for which the curve defined by func is closest to the point xy.

    Parameters
    ----------
    func : Callable
        A function of a single variable. Returns a PointArray.
    v0 : Number
        The initial guess for the variable value.
    v1 : Number
        The second guess for the variable value.
    xy : PointArray
        The point for which the curve should be closest to.
    tolerance : Number or PointArray
        The tolerance for the distance between the curve and the point.
    p0 : Optional[PointArray]
        The point on the curve at v0. If None, it is calculated by calling func(v0).
    p1 : Optional[PointArray]
        The point on the curve at v1. If None, it is calculated by calling func(v1).
    """

    if p0 is None:
        p0 = func((v0, ))
    if p1 is None:
        p1 = func((v1, ))

    num_iter = 0
    best_solution = None
    while True:
        tol_v = (v1 - v0) / norm((p1 - p0) / tolerance)
        distance = norm(p1 - xy)
        if best_solution is None or distance < best_solution.distance:
            best_solution = Solution(v1, p1, distance, tol_v)
        else:
            return best_solution.value, best_solution.point, best_solution.tol_value, num_iter
        p_target, slope = get_closest_point_on_line(p0, p1, xy)
        if norm((p1 - p_target) / tolerance) < 1 or num_iter >= max_iter:
            return v1, p1, tol_v, num_iter
        else:
            overshoot = norm(p1 - p0) / norm(p_target - p0)
            v2 = v0 + (v1 - v0) / overshoot
            num_iter += 1
            p2 = func((v2, ))
            v0, v1 = v1, v2
            p0, p1 = p1, p2


def solve_single_point_with_two_variables(func: Callable, v0, v1, w0, w1, xy: PointArray, tolerance: float = 1,
                                          max_iter: int = 10,
                                          p0: Optional[PointArray] = None, p1: Optional[PointArray] = None
                                          ) -> (float, float, PointArray, int):
    """
    Find the variable values for which the curve defined by func is closest to the point xy.

    Parameters
    ----------
    func : Callable
        A function of two variables. Returns a PointArray.
    v0 : float
        The initial guess for the first variable value.
    v1 : float
        The second guess for the first variable value.
    w0 : float
        The initial guess for the second variable value.
    w1 : float
        The second guess for the second variable value.
    xy : PointArray
        The point for which the curve should be closest to.
    tolerance : float
        The tolerance for the distance between the curve and the point.
    p0 : Optional[PointArray]
        The point on the curve at v0, w0. If None, it is calculated by calling func(v0, w0).
    p1 : Optional[PointArray]
        The point on the curve at v1, w1. If None, it is calculated by calling func(v1, w1).
    """

    if p0 is None:
        p0 = func(v0, w0)
    if p1 is None:
        p1 = func(v1, w1)

    # by convention, v0 affects x (and maybe y) and w0 affects y (and maybe x)
    if func(v0, w0).x == func(v1, w0).x and func(v0, w0).y == func(v0, w1).y:
        return v1, w1, p1, 0

    # check if each variable affects only one coordinate
    # if so, we can solve the two variables independently using solve_single_point_on_curve
    if func(v0, w0).x == func(v1, w0).x and func(v0, w0).y == func(v0, w1).y:
        v, p_v, num_iter_v = solve_single_point_on_curve(lambda x: func(x, w0), v0, v1, xy)
        w, p_w, num_iter_w = solve_single_point_on_curve(lambda y: func(v, y), w0, w1, xy)
        p = func(v, w)
        return v, w, p, num_iter_v + num_iter_w


    num_iter = 0
    closest_value = None
    closest_distance = None
    closest_point = None

    # this time we are not constrained to a single curve. playing with the two variables can bring us to any point
    # therefore get_closest_point_on_line is not used
    # use standard min finder:
    from scipy.optimize import minimize
    def distance(vw):
        return norm(func(vw[0], vw[1]) - xy)

