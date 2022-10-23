import numpy as np

from typing import Any
from .utils import is_numeric_scalar
from pyquibbler.utilities.numpy_original_functions import \
    np_log10, np_abs, np_vectorize, np_maximum, np_minimum, np_round


# should be a number larger than the max number of digits of np.int64, but not
# too large because then np.round fails.
INFINITE_NUMBER_OF_DIGITS = 100


def number_of_digits(value: Any):
    """
    Counts the minimal number of decimal digits needed to fully represent a number.

    Uses `str` (not very fast).
    """
    s = str(value)
    before_e = s.split('e')[0]
    return len(before_e) - before_e.__contains__('.')


def round_if_precision_is_not_inf(value, decimals):
    if -INFINITE_NUMBER_OF_DIGITS < decimals < INFINITE_NUMBER_OF_DIGITS:  # check not inf
        return np_round(value, decimals)

    return value


def floor_log10(value):
    """
    Return the number of order of magnitudes of value.
    When value is very close to 0, INFINITE_NUMBER_OF_DIGITS is returned.
    """
    with np.errstate(divide='ignore'):
        num_digits = np.int64(np.floor(np_log10(np_abs(value))))
    num_digits = np_minimum(num_digits, INFINITE_NUMBER_OF_DIGITS)
    num_digits = np_maximum(num_digits, -INFINITE_NUMBER_OF_DIGITS)
    return num_digits


def round_to_num_digits(value, num_digits):
    """
    Round a scalar or an array to the specified number of digits.
    """
    d = num_digits - floor_log10(value) - 1
    if is_numeric_scalar(value):
        return round_if_precision_is_not_inf(value, d)
    else:
        rounded_value_as_array = np_vectorize(round_if_precision_is_not_inf)(value, d)
        if not isinstance(value, np.ndarray):
            rounded_value_as_array = type(value)(rounded_value_as_array.tolist())
        return rounded_value_as_array
