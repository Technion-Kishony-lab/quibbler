import numpy as np
import pytest

from pyquibbler import iquib, Quib
from pyquibbler.assignment.assignment import AssignmentWithTolerance
from pyquibbler.path import PathComponent


def test_assignment_do_not_change_each_other():
    a = iquib([1, 2])
    a.assign([10, 20, 30])
    a[1] = 21
    assert a.handler.overrider.get(()).value == [10, 20, 30], "sanity"
    a.get_value()

    assert a.handler.overrider.get(()).value == [10, 20, 30]


def test_assignment_with_tolerance():
    a = iquib(np.array([1., 2.]))
    b: Quib = a * 100

    assignment = AssignmentWithTolerance.from_value_path_tolerance(
        value=123.456789,
        path=[PathComponent(np.ndarray, 0)],
        tolerance=5.)

    b.handler.apply_assignment(assignment)

    assert a.handler.overrider.get(assignment.remove_class_from_path()).value == 1.23
