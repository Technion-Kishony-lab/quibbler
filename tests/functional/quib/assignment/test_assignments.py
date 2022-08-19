import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.assignment import AssignmentWithTolerance
from pyquibbler.path import PathComponent


def test_assignment_do_not_change_each_other():
    a = iquib([1, 2])
    a.assign([10, 20, 30])
    a[1] = 21
    assert a.handler.overrider.get(()).value == [10, 20, 30], "sanity"
    a.get_value()

    assert a.handler.overrider.get(()).value == [10, 20, 30]


@pytest.mark.parametrize(['x0', 'a', 'b', 'new_y', 'new_dy', 'component', 'expected'], [
    (10., 1., 0., 10.123456, 0.005, [], 10.12),
    (10., 1., 10., 10.123456, 0.005, [], 0.12),
    (10., 0.1, 0., 10.123456, 0.005, [], 101.2),
    (10., 10., 0., 10.123456, 0.005, [], 1.012),
    (np.array([10., 20.]), 10., 0., 10.123456, 0.005, 0, 1.012),
])
def test_assignment_with_tolerance(x0, a, b, new_y, new_dy, component, expected):
    x = iquib(x0)
    y = a * x + b

    assignment = AssignmentWithTolerance.from_value_path_tolerance(
        value=new_y,
        path=[] if component == [] else [PathComponent(y.get_type(), component)],
        tolerance=new_dy)

    y.handler.apply_assignment(assignment)
    assert x.handler.overrider.get(assignment.remove_class_from_path()).value == expected
