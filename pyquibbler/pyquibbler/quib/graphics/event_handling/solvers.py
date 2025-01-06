from typing import Callable, Optional

import pytest
from numpy.linalg import norm

from pyquibbler.quib.graphics.event_handling.utils import get_closest_point_on_line
from pyquibbler.quib.types import PointArray


def solve_single_point_on_curve(func: Callable, v0, v1, xy: PointArray, tolerance: float = 1,
                                max_iter: int = 10,
                                p0: Optional[PointArray] = None, p1: Optional[PointArray] = None
                                ) -> (float, PointArray, int):
    """
    Find the variable value for which the curve defined by func is closest to the point xy.

    Parameters
    ----------
    func : Callable
        A function of a single variable. Returns a PointArray.
    v0 : float
        The initial guess for the variable value.
    v1 : float
        The second guess for the variable value.
    xy : PointArray
        The point for which the curve should be closest to.
    tolerance : float
        The tolerance for the distance between the curve and the point.
    p0 : Optional[PointArray]
        The point on the curve at v0. If None, it is calculated by calling func(v0).
    p1 : Optional[PointArray]
        The point on the curve at v1. If None, it is calculated by calling func(v1).
    """

    if p0 is None:
        p0 = func(v0)
    if p1 is None:
        p1 = func(v1)

    num_iter = 0
    closest_value = None
    closest_distance = None
    closest_point = None
    while True:
        distance = norm(p1 - xy)
        if closest_distance is None or distance < closest_distance:
            closest_distance = distance
            closest_point = p1
            closest_value = v1
        else:
            return closest_value, closest_point, num_iter
        p_target, slope = get_closest_point_on_line(p0, p1, xy)
        if norm(p1 - p_target) < tolerance or num_iter >= max_iter:
            return v1, p1, num_iter
        else:
            overshoot = norm(p1 - p0) / norm(p_target - p0)
            v2 = v0 + (v1 - v0) / overshoot
            num_iter += 1
            p2 = func(v2)
            v0, v1 = v1, v2
            p0, p1 = p1, p2


@pytest.mark.parametrize('func, v0, v1, xy, expected_v, accuracy, expected_nun_iter, name', [
    (lambda x: PointArray([x, x]), 0, 30, PointArray([30, 30]), 30, 1, 0, 'linear, exact'),
    (lambda x: PointArray([x, x]), 0, 30, PointArray([25, 35]), 30, 1, 0, 'linear, exact perpendicular'),
    (lambda x: PointArray([x, x]), 0, 10, PointArray([30, 30]), 30, 1, 1, 'linear, undershoot'),
    (lambda x: PointArray([x, x**2 / 10]), 0, 30, PointArray([20, 40]), 20, 1, 3, 'non-linear exact'),
    (lambda x: PointArray([x, x**2 / 10]), 0, 30, PointArray([20+8, 40-2]), 20, 1, 4, 'non-linear exact'),
    (lambda x: PointArray([x, 10]), 0, 30, PointArray([30, 40]), 30, 1, 0, 'horizontal line, linear, exact'),
    (lambda x: PointArray([x, 10]), 0, 20, PointArray([30, 40]), 30, 1, 1, 'horizontal line, linear, undershoot'),
    (lambda x: PointArray([10, x]), 0, 30, PointArray([40, 30]), 30, 1, 0, 'vertical line, linear, exact'),
    (lambda x: PointArray([10, x]), 0, 20, PointArray([40, 30]), 30, 1, 1, 'vertical line, linear, undershoot'),
    (lambda x: PointArray([x, x ** 2 / 10]), 30, 20, PointArray([0, -10]), 0, 4, 3, 'non-linear with minimum'),
    (lambda x: PointArray([0, x ** 2 / 10]), 30, 10, PointArray([0, -10]), 0, 4, 3, 'back and forth line'),
    (lambda x: PointArray([0, 0]), 30, 10, PointArray([0, 10]), 10, 1, 0, 'return p1 if not moving'),
])
def test_solve_single_point_on_curve(func, v0, v1, xy, expected_v, accuracy, expected_nun_iter, name):
    """
    Test the solve_single_point_on_curve function.
    """
    result, point, num_iter = solve_single_point_on_curve(func, v0, v1, xy)
    assert abs(result - expected_v) <= accuracy, f'{name}: result is {result}, expected {expected_v}'
    assert num_iter == expected_nun_iter, f'{name}: num_iter is {num_iter}, expected {expected_nun_iter}'


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

