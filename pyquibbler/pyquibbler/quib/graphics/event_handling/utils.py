from typing import Tuple

import numpy as np
from matplotlib.axes import Axes

from pyquibbler.quib.types import PointXY
from pyquibbler.utilities.numpy_original_functions import np_vectorize

EPSILON = 1e-6


def get_closest_point_on_line(xy1: PointXY, xy2: PointXY, xy_p: PointXY) -> Tuple[PointXY, PointXY]:
    """
    Find the closest point along a line to a specified point.

    xy1, xy2 are two Points, defining a straight line
    xy_p is an arbitrary Point, not necessarily on the line

    returns a Point(x, y) which is on the line and closest to the xy_point.
    also return `slope`: the normalized dx, dy of the line
    """
    d = xy2 - xy1
    d_s = d * d

    sum_d_s = d_s.x + d_s.y
    sqrt_d_s = np.sqrt(sum_d_s)
    if sum_d_s < EPSILON:
        return xy1, PointXY(1, 1)
    else:
        x = (d.x * d.y * (xy_p.y - xy1.y) + d_s.x * xy_p.x + d_s.y * xy1.x) / sum_d_s
        y = (d.x * d.y * (xy_p.x - xy1.x) + d_s.y * xy_p.y + d_s.x * xy1.y) / sum_d_s

    return PointXY(x, y), PointXY(d.x / sqrt_d_s, d.y / sqrt_d_s)


def get_closest_point_on_line_in_axes(ax: Axes, xy1: PointXY, xy2: PointXY, xy_p: PointXY) -> Tuple[PointXY, PointXY]:
    """
    Find the closest point along a line to a specified point, within the coordinates of a specified axes.

    xy1, xy2 are two points, defining a straight line
    xy_p is an arbitrary point

    returns a point, PointXY, which is on the line and closest to xy_p.
    also return `slope`: the normalized dx, dy of the line
    """

    transform = ax.transData.transform
    xy, slope = get_closest_point_on_line(
        PointXY.from_array_like(transform(xy1)),
        PointXY.from_array_like(transform(xy2)),
        PointXY.from_array_like(transform(xy_p)),
    )

    return PointXY.from_array_like(ax.transData.inverted().transform(xy)), slope


def get_intersect_between_two_lines(a_x1, a_y1, a_x2, a_y2, b_x1, b_y1, b_x2, b_y2):

    # Calculate the denominator of the equations of the two lines
    denominator = ((a_x1-a_x2)*(b_y1-b_y2)) - ((a_y1-a_y2)*(b_x1-b_x2))

    # If the denominator is zero, the lines are parallel and do not intersect
    if denominator == 0:
        return None, None

    # Calculate the x and y coordinates of the point of intersection
    x = (((a_x1*a_y2-a_y1*a_x2)*(b_x1-b_x2))-((a_x1-a_x2)*(b_x1*b_y2-b_y1*b_x2))) / denominator
    y = (((a_x1*a_y2-a_y1*a_x2)*(b_y1-b_y2))-((a_y1-a_y2)*(b_x1*b_y2-b_y1*b_x2))) / denominator

    return x, y


def get_intersect_between_two_lines_in_axes(ax: Axes,
                                            a1: PointXY, a2: PointXY,
                                            b1: PointXY, b2: PointXY) -> Tuple[PointXY, PointXY]:
    """
    Find the closest point along a line to a specified point, within the coordinates of a specified axes.

    a1, a2 are two points, defining a straight line a.
    b1, b2 are two points, defining a straight line b.

    returns a point, PointXY, which is on the intersection of the two lines.
    also return difference of slopes: of the two lines.
    """
    a1, a2, b1, b2 = ax.transData.transform([a1, a2, b1, b2])

    xy = get_intersect_between_two_lines(*a1, *a2, *b1, *b2)

    # TODO: calculate correct error of intersect
    err = PointXY(1, 1)
    return PointXY.from_array_like(ax.transData.inverted().transform(xy)), err


def get_sqr_distance_in_axes(ax: Axes, xy1: PointXY, xy2: PointXY) -> float:
    """
    Returns the square distance in pixels between two points in axes
    """

    xy1 = PointXY.from_array_like(ax.transData.transform(xy1))
    xy2 = PointXY.from_array_like(ax.transData.transform(xy2))
    d = xy1 - xy2

    return d.x ** 2 + d.y ** 2


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

    return np_vectorize(_func, *args, otypes=otypes, **kwargs)
