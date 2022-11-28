from typing import Tuple

import numpy as np
from matplotlib.axes import Axes

from pyquibbler.quib.types import PointXY

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

    xy_line1, xy_line2 are two points, defining a straight line
    xy_point is an arbitrary point

    returns a point (x, y) which is on the line and closest to the xy_point.
    also return `slope`: the normalized dx, dy of the line
    """

    xy, slope = get_closest_point_on_line(
        PointXY.from_array_like(ax.transData.transform(xy1)),
        PointXY.from_array_like(ax.transData.transform(xy2)),
        PointXY.from_array_like(ax.transData.transform(xy_p)),
    )

    return PointXY.from_array_like(ax.transData.inverted().transform(xy)), slope
