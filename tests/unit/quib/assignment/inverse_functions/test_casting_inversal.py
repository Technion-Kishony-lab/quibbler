import numpy as np
import pytest

from pyquibbler import iquib, q
from pyquibbler.quib import ElementWiseFunctionQuib, FunctionQuib
from pyquibbler.quib.assignment import Assignment

def inverse(function_quib: FunctionQuib, value, path):
    assignment = Assignment(value, path)
    inversions = function_quib.get_inversions_for_assignment(assignment=assignment)
    for inversion in inversions:
        inversion.apply()


@pytest.mark.parametrize("value, function, assigned_value, expected_value", [
    (1, str, '17', 17),
    (1.7, str, '17.3', 17.3),
    ([1,2,3], str, '[4,5]', [4,5]),
    (1.3, int, 5, 5.),
    (1, float, 4.3, 4),
    ('3.4', float, 4.3, '4.3'),
    ('3', int, 4, '4'),
], ids=[
    "int -> str",
    "float -> str",
    "list -> str",
    "float -> int",
    "int -> float",
    "str -> float",
    "str -> int",
])
def test_inverse_casting(value, function, assigned_value, expected_value):
    path = []
    q0 = iquib(value)
    q1 = q(function,q0)
    q1.assign_value(assigned_value)
    assert q0.get_value() == expected_value
