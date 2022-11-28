import numbers
import numpy as np

from matplotlib.axes import Axes
from datetime import datetime
from matplotlib.dates import num2date

from pyquibbler.quib.types import PointXY
from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION


def get_axes_x_y_tolerance(ax: Axes) -> PointXY:
    """
    Return the mouse resolution in x-axis and y-axis in which a point can be specified in a given axes.
    """
    n = GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val
    if n is None:
        return PointXY(None, None)
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    return PointXY((xlim[1] - xlim[0]) / n, (ylim[1] - ylim[0]) / n)


def is_scalar_np(obj) -> bool:
    """
    Check if obj is a scalar, in the sense that np.shape(obj) = () [but without running np.shape]
    """
    if np.isscalar(obj):
        return True
    if isinstance(obj, dict):
        return True
    try:
        len(obj)
    except TypeError:
        return True
    return False


def is_numeric_scalar(data) -> bool:
    return isinstance(data, numbers.Number)


def is_integer_scalar(data) -> bool:
    return isinstance(data, numbers.Integral)


def is_array_of_size_one(data) -> bool:
    return isinstance(data, (np.ndarray, list)) and np.size(data) == 1


def convert_array_of_size_one_to_scalar(data):
    while is_array_of_size_one(data):
        data = data[0]
    return data


def convert_scalar_value(current_value, assigned_value):
    """
    Convert an assigned_value to match the type of a current_value.
    """
    if is_integer_scalar(current_value):
        return type(current_value)(round(assigned_value))
    if isinstance(current_value, datetime) and isinstance(assigned_value, float):
        return num2date(assigned_value).replace(tzinfo=None)
    return type(current_value)(assigned_value)
