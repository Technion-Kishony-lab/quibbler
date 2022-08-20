import numpy as np

from typing import Any
from .utils import is_scalar


# should be a number larger than the max number of digits of np.int64, but not
# too large because then np.round fails.
from pyquibbler.utilities.numpy_original_functions import np_log10, np_abs, np_vectorize, np_maximum, np_minimum, np_round

INFINITE_NUMBER_OF_DIGITS = 100


def number_of_digits(value: Any):
    s = str(value)
    before_e = s.split('e')[0]
    return len(before_e) - before_e.__contains__('.')


def round_if_precision_is_not_inf(value, decimals):
    if -INFINITE_NUMBER_OF_DIGITS < decimals < INFINITE_NUMBER_OF_DIGITS:  # check not inf
        return np_round(value, decimals)

    return value


def get_number_of_digits(value):
    # with warnings.catch_warnings():
    #     warnings.filterwarnings("ignore")  # divide by zero encountered in log10
    with np.errstate(divide='ignore'):
        num_digits = np.int64(np.floor(np_log10(np_abs(value))))
    num_digits = np_minimum(num_digits, INFINITE_NUMBER_OF_DIGITS)
    num_digits = np_maximum(num_digits, -INFINITE_NUMBER_OF_DIGITS)
    return num_digits


def round_to_num_digits(value, num_digits):
    d = num_digits - get_number_of_digits(value) - 1
    if is_scalar(value):
        return round_if_precision_is_not_inf(value, d)
    else:
        return np_vectorize(round_if_precision_is_not_inf)(value, d)
