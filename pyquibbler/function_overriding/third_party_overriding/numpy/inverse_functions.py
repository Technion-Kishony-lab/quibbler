import numpy as np
from typing import Callable
pi = np.pi


def inv_sin(new_y, x):
    """
    assuming y = sin(x) and y->new_y, find corresponding new_x such that
    new_y = sin(new_x) and new_x is in the same period as x
    """

    n = np.floor(x / pi + 0.5)
    return -(np.mod(n, 2) * 2 - 1) * np.arcsin(new_y) + n * pi


def inv_cos(new_y, x):
    """
    assuming y = cos(x) and y->new_y, find corresponding new_x such that
    new_y = cos(new_x) and new_x is in the same period as x
    """

    n = np.floor(x / pi)
    return -(np.mod(n, 2) * 2 - 1) * (np.arccos(new_y) - pi / 2) + n * pi + pi / 2


def inv_tan(new_y, x):
    """
    assuming y = tan(x) and y->new_y, find corresponding new_x such that
    new_y = tan(new_x) and new_x is in the same period as x
    """

    n = np.floor(x / pi + 0.5)
    return np.arctan(new_y) + n * pi


def keep_sign(inv_func: Callable) -> Callable:
    def sign_keeping(new_y, x):
        return np.sign(x) * inv_func(new_y)

    return sign_keeping
