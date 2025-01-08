import numpy as np
import pytest

from pyquibbler.quib.graphics.event_handling.solvers import solve_single_point_on_curve, \
    decompose_vector_into_two_components, solve_single_point_with_two_variables
from pyquibbler.quib.types import PointArray
from pyquibbler.utilities.numpy_original_functions import np_array


@pytest.mark.parametrize(['point_nd', 'other', 'expected'], [
    (PointArray([[1, 2]]), PointArray([[3, 4]]), PointArray([[4, 6]])),
    (PointArray([[1, 2]]), (3, 4), PointArray([[4, 6]])),
    (PointArray([[1, 2]]), 3, PointArray([[4, 5]])),
])
def test_point_array_add(point_nd, other, expected):
    result = point_nd + other
    assert np.array_equal(result, expected)


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


def test_decompose_vector_into_two_components():
    v = PointArray((1, 3))
    w = PointArray((5, 2))
    xy = PointArray((7, 8))
    c, _ = decompose_vector_into_two_components([v, w], xy)
    assert np.array_equal(c[0] * v + c[1] * w, xy)


@pytest.mark.parametrize(['func', 'v0', 'v1', 'w0', 'w1', 'xy', 'accuracy', 'expected_vw', 'expected_nun_iter', 'name'], [
    (lambda v, w: (v, w), 0, 30, 0, 30, (30, 30), 1, None, 0, 'linear, exact'),
    (lambda v, w: (v, w), 0, 60, 0, 6, (30, 30), 1, None, 0, 'linear, overshoot and undershoot'),
    (lambda v, w: (v, w), 0, 60, 0, 6, (25, 35), 1, None, 0, 'linear, exact unequal'),
    (lambda v, w: (v**2, w), 3, 3.5, 0, 30, (25, 40), 1, None, 1, 'non-linear'),
    (lambda v, w: (v**2 + 5*w, w**2 + 2*v), 1.5, 4, 2.5, 5, (19, 13), 1, None, 1, 'non-linear, two variables'),
    (lambda v, w: ((v ** 2 + 5 * w) * 100, (w ** 2 + 2 * v) * 100), 1.5, 1.6, 2.5, 2.6, (1900, 1300), 1, None, 1, 'non-linear, two variables, high res'),
    (lambda v, w: ((v ** 3 + 5 * w) * 100, (w ** 4 + 2 * v) * 100), 1.5, 1.2001, 2.5, 2.6, (2300, 8500), 1, None, 2, 'non-linear, two variables'),
    (lambda v, w: (v+w, 3*(v+w)), 5, 6, 5, 6, (12, 36), 0.1, None, None, 'dependent variables'),
    (lambda v, w: (v + w, 3 * (v + w)), 5, 6, 5, 6, (12+6, 36-2), 0.1, (6, 6), None, 'dependent variables, not on line'),
    (lambda v, w: (v + w, v - w), 3, 3, 3, 4, (2, -2), 0.1, (3, 2), None, 'dependent variables, only one var vahnges'),
])
def test_solve_single_point_with_two_variables(func, v0, v1, w0, w1, xy, accuracy, expected_vw, expected_nun_iter, name):
    def _func(vw):
        v, w = vw
        sol = func(v, w)
        print(vw, sol)
        return PointArray(sol)

    xy = PointArray(xy)
    result, point, tol, num_iter = solve_single_point_with_two_variables(
        _func, np_array([v0, w0]), np_array([v1, w1]), xy)
    if expected_vw is not None:
        assert np.all(np.abs(result - expected_vw) <= accuracy), f'{name}: result is {result}, expected {expected_vw}'
    else:
        assert np.all(np.abs(point - xy) <= accuracy), f'{name}: result is {result}, expected {xy}'
    if expected_nun_iter is not None:
        assert num_iter == expected_nun_iter, f'{name}: num_iter is {num_iter}, expected {expected_nun_iter}'
