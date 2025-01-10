from typing import Tuple

import numpy as np
from matplotlib.axes import Axes

from pyquibbler.quib.types import PointArray
from pyquibbler.utilities.numpy_original_functions import np_vectorize

EPSILON = 1e-6


def get_closest_point_on_line(xy1: PointArray, xy2: PointArray, xy_p: PointArray
                              ) -> Tuple[PointArray, PointArray]:
    """
    Find the closest point along a line to a specified point.

    xy1, xy2 are two Points, defining a straight line
    xy_p is an arbitrary Point, not necessarily on the line

    returns:
        Point(x, y):
            the point on the line closest to the xy_point.
        slope:
            the normalized dx, dy of the line
    """

    d = xy2 - xy1
    d_s = d * d

    sum_d_s = d_s[0] + d_s[1]
    sqrt_d_s = np.sqrt(sum_d_s)

    if sum_d_s < EPSILON:
        return xy1, PointArray([1, 1])

    x = (d[0] * d[1] * (xy_p[1] - xy1[1]) + d_s[0] * xy_p[0] + d_s[1] * xy1[0]) / sum_d_s
    y = (d[0] * d[1] * (xy_p[0] - xy1[0]) + d_s[1] * xy_p[1] + d_s[0] * xy1[1]) / sum_d_s

    return PointArray([x, y]), PointArray([d[0] / sqrt_d_s, d[1] / sqrt_d_s])


def get_closest_point_on_line_in_axes(ax: Axes, xy1: PointArray, xy2: PointArray, xy_p: PointArray
                                      ) -> Tuple[PointArray, PointArray]:
    """
    Find the closest point along a line to a specified point, within the coordinates of a specified axes.

    xy1, xy2 are two points, defining a straight line
    xy_p is an arbitrary point

    returns a point, PointArray, which is on the line and closest to xy_p.
    also return `slope`: the normalized dx, dy of the line
    """

    transform = ax.transData.transform
    xy, slope = get_closest_point_on_line(
        PointArray(transform(xy1)),
        PointArray(transform(xy2)),
        PointArray(transform(xy_p)),
    )

    return PointArray(ax.transData.inverted().transform(xy)), slope


def get_intersect_between_two_lines(a_x1, a_y1, a_x2, a_y2, b_x1, b_y1, b_x2, b_y2):

    # Calculate the denominator of the equations of the two lines
    denominator = (a_x1 - a_x2) * (b_y1 - b_y2) - (a_y1 - a_y2) * (b_x1 - b_x2)

    # If the denominator is zero, the lines are parallel and do not intersect
    if denominator == 0:
        return None, None

    # Calculate the x and y coordinates of the point of intersection
    x = ((a_x1 * a_y2 - a_y1 * a_x2) * (b_x1 - b_x2) - (a_x1 - a_x2) * (b_x1 * b_y2 - b_y1 * b_x2)) / denominator
    y = ((a_x1 * a_y2 - a_y1 * a_x2) * (b_y1 - b_y2) - (a_y1 - a_y2) * (b_x1 * b_y2 - b_y1 * b_x2)) / denominator

    return x, y


def get_intersect_between_two_lines_in_axes(ax: Axes,
                                            a1: PointArray, a2: PointArray,
                                            b1: PointArray, b2: PointArray) -> Tuple[PointArray, PointArray]:
    """
    Find the closest point along a line to a specified point, within the coordinates of a specified axes.

    a1, a2 are two points, defining a straight line a.
    b1, b2 are two points, defining a straight line b.

    returns a point, PointArray, which is on the intersection of the two lines.
    also return difference of slopes: of the two lines.
    """
    a1, a2, b1, b2 = ax.transData.transform([a1, a2, b1, b2])

    xy = get_intersect_between_two_lines(*a1, *a2, *b1, *b2)

    # TODO: calculate correct error of intersect
    err = PointArray([1, 1])
    return PointArray(ax.transData.inverted().transform(xy)), err


def get_sqr_distance_in_axes(ax: Axes, xy1: PointArray, xy2: PointArray) -> float:
    """
    Returns the square distance in pixels between two points in axes
    """

    xy1 = PointArray(ax.transData.transform(xy1))
    xy2 = PointArray(ax.transData.transform(xy2))
    d = xy1 - xy2

    return d[0] ** 2 + d[1] ** 2


def skip_vectorize(func, *args, otypes=0, **kwargs):
    """
    Like vectorize, but skips the vectorization if the input is None
    """
    if otypes == 0:
        otypes = [object]

    def _func(*a, **k):
        if a[0] is None:
            return None
        return func(*a, **k)

    vectorized_func = np_vectorize(_func, *args, otypes=otypes, **kwargs)

    def _vectorize_to_point_array(*a, **k):
        return PointArray(vectorized_func(*a, **k))

    return _vectorize_to_point_array


def _get_overshoot(p0: PointArray, p1: PointArray, p: PointArray) -> float:
    """
    Assuming that p is on the line defined by p0 and p1, calculate the distance of p from p0, in
    the direction of p1 and in units of the distance between p0 and p1.
    """
    # .         dis=0               dis=1
    #          xy1                 xy2
    # ---------|-------------------|---------
    #   |                   |             |
    #   |                   |             |
    #   xy_p                xy_p          xy_p
    #   dis<0               0<dis<1       dis>1
    #

    dp = p1 - p0

    if np.all(dp == 0):
        return 0.

    if abs(dp[0]) > abs(dp[1]):
        return (p[0] - p0[0]) / dp[0]
    else:
        return (p[1] - p0[1]) / dp[1]
