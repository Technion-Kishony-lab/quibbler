import numpy as np
import pytest
from copy import deepcopy

from pyquibbler.assignment import Assignment, AssignmentSimplifier
from pyquibbler.path import deep_set
from pyquibbler.path.path_component import Path, PathComponent
from pyquibbler.quib.specialized_functions.iquib import create_iquib


def is_path_simple(path: Path):
    if len(path) != 1:
        return False
    component = path[0].component
    if isinstance(component, tuple) and len(component) == 1:
        return False
    if not isinstance(component, tuple):
        component = (component, )
    return all(isinstance(index, (int, slice, np.int32, np.int64)) for index in component)


@pytest.mark.parametrize("assigned_value, assigned_path, data, should_simplify", [
    ([3], 1, [1, [2]], False),
    (3, [1, 2], np.array([10, 20, 30]), False),
    (3, [2], np.array([10, 20, 30]), True),
    (100, ([2], [3]), np.arange(12).reshape(3, 4), True),
    (100, (np.array([2]), [3]), np.arange(12).reshape(3, 4), True),
    (np.array([100]), (np.array([2]), [3]), np.arange(12).reshape(3, 4), True),
    ([100], (np.array([2]), [3]), np.arange(12).reshape(3, 4), True),
    ([100], ([False, True, False], [False, False, True, False]), np.arange(12).reshape(3, 4), True),
    ([100, 101, 102], ([[False, False, False], [True, True, True]],), np.arange(6).reshape(2, 3), True),
], ids=[
    "nested list",
    "not single value",
    "single value",
    "two-dimensional",
    "two-dimensional with ndarray",
    "simplify assigned_value",
    "simplify assigned_value list",
    "bool indexing",
    "bool whole-array indexing",
])
def test_assignment_simplify(assigned_value, assigned_path, data, should_simplify):
    assignment = Assignment(assigned_value, [PathComponent(assigned_path)])
    simplified_assignment = AssignmentSimplifier(deepcopy(assignment), data).simplify()

    data_original_assignment = deep_set(data, assignment.path, assignment.value)
    data_simplified_assignment = deep_set(data, simplified_assignment.path, simplified_assignment.value)

    if isinstance(data_simplified_assignment, np.ndarray):
        assert np.array_equal(data_simplified_assignment, data_original_assignment)
    else:
        assert data_simplified_assignment == data_original_assignment

    if should_simplify:
        assert is_path_simple(simplified_assignment.path)
        assert not isinstance(simplified_assignment.value, np.ndarray)


def test_assignment_simplify_into_list_quib():
    q = create_iquib([1, [2]])
    q[1] = [3]
    assert q.get_value() == [1, [3]]
