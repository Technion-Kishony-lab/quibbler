import numpy as np
import pytest
from pytest import fixture

from pyquibbler.assignment import Overrider, Assignment
from pyquibbler.path.path_component import PathComponent
from pyquibbler.path.data_accessing import FailedToDeepAssignException


@fixture
def overrider():
    return Overrider()


def test_overrider_add_assignment_and_override(overrider):
    overrider.add_assignment(Assignment(value=0, path=[PathComponent(0)]))
    new_data = overrider.override([1])

    assert new_data == [0]


def test_overrider_with_global_override(overrider):
    overrider.add_assignment(Assignment(value=[2, 3, 4], path=[]))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [2, 3, 4]


def test_overrider_with_global_override_and_partial_assignments(overrider):
    overrider.add_assignment(Assignment(value=[2, 3, 4], path=[]))
    overrider.add_assignment(Assignment(value=100, path=[PathComponent(0)]))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [100, 3, 4]


def test_overrider_with_field_assignment(overrider):
    dtype = np.dtype([('name', 'U10'), ('age', int)])
    overrider.add_assignment(Assignment(value=1, path=[PathComponent('age')]))
    new_data = overrider.override(np.array([('maor2', 23)], dtype=dtype))

    assert new_data['age'] == 1


def test_overrider_with_field_assignment_and_indices(overrider):
    dtype = np.dtype([('name', 'U10'), ('age', int)])
    overrider.add_assignment(Assignment(value=1, path=[PathComponent((0, 0)), PathComponent("age")]))
    new_data = overrider.override(np.array([[('maor2', 23)]], dtype=dtype))

    assert np.array_equal(new_data, np.array([[('maor2', 1)]], dtype=dtype))


def test_overrider_remove_assignment(overrider):
    overrider.add_assignment(Assignment(value=[1, 1], path=[]))
    overrider.add_assignment(Assignment.create_default([PathComponent(1)]))
    new_data = overrider.override([0, 0])

    assert new_data == [1, 0]


def test_overrider_raises_exception_when_out_of_bounds_on_active_assignment(overrider):
    overrider.add_assignment(Assignment(value=10, path=[PathComponent(10)]))

    with pytest.raises(FailedToDeepAssignException, match='.*'):
        overrider.override([])


@pytest.mark.regression
def test_overrider_doesnt_raise_exception_when_out_of_bounds_on_non_active_assignment(overrider):
    overrider.add_assignment(Assignment(value=10, path=[PathComponent(10)]))
    # we create another assignment to make the previous not the active assignment
    overrider.add_assignment(Assignment(value=0, path=[]))

    # We only truly want to make sure the above assignment didn't cause an exception
    new_data = overrider.override([])

    assert new_data == 0


@pytest.mark.regression
def test_overrider_doesnt_raise_exception_when_wrong_type(overrider):
    overrider.add_assignment(Assignment(value=1, path=[PathComponent('a')]))
    # we create another assignment to make the previous not the active assignment
    overrider.add_assignment(Assignment(value=0, path=[]))

    # We only truly want to make sure the above assignment didn't cause an exception
    new_data = overrider.override([])

    assert new_data == 0


def test_overrider_keeps_order(overrider):
    overrider.add_assignment(Assignment(value=[5], path=[]))
    overrider.add_assignment(Assignment.create_default([PathComponent(0)]))
    overrider.add_assignment(Assignment(value=[10], path=[]))

    # We only truly want to make sure the above assignment didn't cause an exception
    new_data = overrider.override([20])

    assert new_data == [10]


@pytest.mark.parametrize("text, expected",[
    ('quib[2] = default', [Assignment.create_default([PathComponent(2)])]),
    ('quib.assign([1, 2])', [Assignment([1, 2], [])]),
    ('quib[2][1] = default', [Assignment.create_default([PathComponent(2), PathComponent(1)])]),
    ('quib[array([2])][[1, 2, 3], 5] = 23', [Assignment(value=23, path=[PathComponent(np.array([2])), PathComponent((
            [1, 2, 3], 5))])]),
    ('quib[1:] = 23', [Assignment(value=23, path=[PathComponent(slice(1, None, None))])]),
    ('quib[1] = 10\nquib[2] = 20', [Assignment(value=10, path=[PathComponent(1)]),
                                    Assignment(value=20, path=[PathComponent(2)])])
])
def test_overrider_loads_assignments_from_text(text, expected):
    overrider = Overrider()
    overrider.load_from_txt(assignments_text=text)
    assert overrider._assignments == expected


def test_overrider_returns_newly_invalidated_paths():
    overrider = Overrider()
    paths = overrider.load_from_txt(assignments_text='quib[1] = 10\nquib[2] = 20')
    assert paths[0] == [PathComponent(1)]
    assert paths[1] == [PathComponent(2)]
