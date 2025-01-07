import numpy as np
import pytest

from pyquibbler.quib.graphics.event_handling.solvers import solve_single_point_on_curve
from pyquibbler.quib.types import PointArray


@pytest.mark.parametrize(['point_nd', 'other', 'expected'], [
    (PointArray([[1, 2]]), PointArray([[3, 4]]), PointArray([[4, 6]])),
    (PointArray([[1, 2]]), (3, 4), PointArray([[4, 6]])),
    (PointArray([[1, 2]]), 3, PointArray([[4, 5]])),
])
def test_point_array_add(point_nd, other, expected):
    result = point_nd + other
    assert np.array_equal(result, expected)
    assert isinstance(result, PointArray)


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
    tuple_func = lambda x: func(x[0])
    result, point, _, num_iter = solve_single_point_on_curve(tuple_func, v0, v1, xy)
    assert abs(result - expected_v) <= accuracy, f'{name}: result is {result}, expected {expected_v}'
    assert num_iter == expected_nun_iter, f'{name}: num_iter is {num_iter}, expected {expected_nun_iter}'

