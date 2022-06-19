import numpy as np
import pytest
from pytest import fixture

from pyquibbler.assignment import Assignment, AssignmentSimplifier
from pyquibbler.path import deep_assign_data_in_path
from pyquibbler.path.path_component import Path, PathComponent


@fixture
def assignment_simplifier():
    return AssignmentSimplifier()


def is_path_simple(path: Path):
    if len(path) != 1:
        return False
    component = path[0].component
    if isinstance(component, tuple) and len(component) == 1:
        return False
    if not isinstance(component, tuple):
        component = (component, )
    return all(isinstance(index, (int, np.int64)) for index in component)


@pytest.mark.parametrize("assigned_value, assigned_path, data, should_simplify", [
    (3, [1, 2], np.array([10, 20, 30]), False),
    (3, [2], np.array([10, 20, 30]), True),
    (100, ([2], [3]), np.arange(12).reshape(3, 4), True),
    (100, (np.array([2]), [3]), np.arange(12).reshape(3, 4), True),
    (np.array([100]), (np.array([2]), [3]), np.arange(12).reshape(3, 4), True),
    ([100], (np.array([2]), [3]), np.arange(12).reshape(3, 4), True),
], ids=[
    "not single value",
    "single value",
    "two-dimensional",
    "two-dimensional with ndarray",
    "simplify assigned_value",
    "simplify assigned_value list",
])
def test(assigned_value, assigned_path, data, should_simplify):
    assignment = Assignment(assigned_value, [PathComponent(np.ndarray, assigned_path)])
    simplied_assignment = AssignmentSimplifier(assignment, data).simplify()

    data_original_assignment = deep_assign_data_in_path(data, assignment.path, assignment.value)
    data_simplified_assignment = deep_assign_data_in_path(data, simplied_assignment.path, simplied_assignment.value)

    assert np.array_equal(data_simplified_assignment, data_original_assignment)

    if should_simplify:
        assert is_path_simple(simplied_assignment.path)
        assert not isinstance(simplied_assignment.value, np.ndarray)
