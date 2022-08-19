import numbers
import warnings
import numpy as np

from typing import Any

from matplotlib.axes import Axes
from datetime import datetime
from matplotlib.dates import num2date

from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION


def get_axes_x_y_tolerance(ax: Axes):
    n = GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val
    if n is None:
        return None, None
    xlim = ax.get_xlim()
    ylim = ax.get_ylim()
    return (xlim[1] - xlim[0]) / n, \
           (ylim[1] - ylim[0]) / n


def number_of_digits(value: Any):
    s = str(value)
    before_e = s.split('e')[0]
    return len(before_e) - before_e.__contains__('.')


def round_if_precision_is_not_inf(value, decimals):
    if -100 < decimals < 100:  # check not inf
        return np.round(value, decimals)

    return value


def is_scalar(data) -> bool:
    return isinstance(data, numbers.Number)


def is_scalar_integer(data) -> bool:
    return isinstance(data, numbers.Integral)


def is_array_of_size_one(data) -> bool:
    return isinstance(data, (np.ndarray, list)) and np.size(data) == 1


def convert_to_array(value: Any):
    if isinstance(value, (list, tuple)):
        return np.array(value)
    return value


def convert_array_of_size_one_to_scalar(data):
    while is_array_of_size_one(data):
        data = data[0]
    return data


def convert_scalar_value(current_value, assigned_value):
    if is_scalar_integer(current_value):
        return type(current_value)(round(assigned_value))
    if isinstance(current_value, datetime) and isinstance(assigned_value, float):
        return num2date(assigned_value).replace(tzinfo=None)
    return type(current_value)(assigned_value)


def get_number_of_digits(value):
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")  # divide by zero encountered in log10
        return np.int64(np.floor(np.log10(np.abs(value))))


def round_to_num_digits(value, num_digits):
    d = num_digits - get_number_of_digits(value) - 1
    if is_scalar(value):
        return round_if_precision_is_not_inf(value, d)
    else:
        return np.vectorize(round_if_precision_is_not_inf)(value, d)

