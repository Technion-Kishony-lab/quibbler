from dataclasses import dataclass

import numpy as np
from typing import Callable, Union, Tuple

from pyquibbler.env import INPUT_AWARE_INVERSION

pi = np.pi


RawInverseFunc = Union[Callable, Tuple[Callable, Callable]]
"""
Specifies a single nominal inverse function, or a tuple of a nominal and an input-dependent inverse function.
"""


@dataclass
class InverseFunc:
    """
    An inverse function.

    For a many-to-one function, we have two ways of inverting: inverting to the nominal value, or inverting
    based on the previous input (requires_previous_input=True/False)

    For a given many-to-one function, we might have an inverse function inverting to the nominal value
    (requires_previous_input=False), or an inverse function inverting to the value closest to the previous value.
    In this second case, we need to supply the previous input ((requires_previous_input=True).

    For a single-argument func, y = func(x), the inverse function is either:
    new_x = inv_func(new_y) [requires_previous_input=False]
    new_x = inv_func(new_y, previous_x)  [requires_previous_input=True]

    For a two-argument func, y = func(x1, x2), we will have two inverse functions, for x1 (given x2)
    and for x2 (given x1). Each of these functions may require previous input:

    x1_new = inv_func(new_y, x2) [requires_previous_input=False]
    x1_new = inv_func(new_y, x2, previous_x1) [requires_previous_input=True]

    x2_new = inv_func(new_y, x1) [requires_previous_input=False]
    x2_new = inv_func(new_y, x1, previous_x2) [requires_previous_input=True]
    """
    inv_func: Callable
    requires_previous_input: bool

    @classmethod
    def from_raw_inverse_func(cls, raw_inverse_func: RawInverseFunc):
        requires_previous_input = False
        if isinstance(raw_inverse_func, tuple):
            if INPUT_AWARE_INVERSION:
                inverse_func = raw_inverse_func[1]
                requires_previous_input = True
            else:
                inverse_func = raw_inverse_func[0]
        else:
            inverse_func = raw_inverse_func
        return cls(inverse_func, requires_previous_input)


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


def inv_power(new_y, power, x):
    """
    assuming y = x^power and y->new_y, find corresponding new_x such that
    new_y = new_x^power. If power is an even int, there are two real solutions, and we choose
    the one with the same size as x
    """
    new_x = new_y ** (1 / power)
    if power % 2 == 0:
        new_x *= np.sign(x)
    return new_x
