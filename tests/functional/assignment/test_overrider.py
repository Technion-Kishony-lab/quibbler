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
    overrider.add_assignment(Assignment(value=0, path=[PathComponent(indexed_cls=np.ndarray, component=0)]))
    new_data = overrider.override([1])

    assert new_data == [0]


def test_overrider_with_global_override(overrider):
    overrider.add_assignment(Assignment(value=[2, 3, 4], path=[]))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [2, 3, 4]


def test_overrider_with_global_override_and_partial_assignments(overrider):
    overrider.add_assignment(Assignment(value=[2, 3, 4], path=[]))
    overrider.add_assignment(Assignment(value=100, path=[PathComponent(indexed_cls=list, component=0)]))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [100, 3, 4]


def test_overrider_with_field_assignment(overrider):
    dtype = [('name', np.compat.unicode, 21), ('age', np.int_)]
    overrider.add_assignment(Assignment(value=1, path=[PathComponent(indexed_cls=np.ndarray, component='age')]))
    new_data = overrider.override(np.array([('maor2', 23)], dtype=dtype))

    assert new_data['age'] == 1


def test_overrider_with_field_assignment_and_indices(overrider):
    dtype = [('name', np.compat.unicode, 21), ('age', np.int_)]
    overrider.add_assignment(Assignment(value=1, path=[PathComponent(indexed_cls=np.ndarray,
                                                                     component=(0, 0)),
                                                       PathComponent(indexed_cls=np.ndarray,
                                                                     component="age")
                                                       ]))
    new_data = overrider.override(np.array([[('maor2', 23)]], dtype=dtype))

    assert np.array_equal(new_data, np.array([[('maor2', 1)]], dtype=dtype))


def test_overrider_remove_assignment(overrider):
    overrider.add_assignment(Assignment(value=[1, 1], path=[]))
    overrider.add_assignment(Assignment.create_default([PathComponent(component=1, indexed_cls=list)]))
    new_data = overrider.override([0, 0])

    assert new_data == [1, 0]


def test_overrider_raises_exception_when_out_of_bounds_on_active_assignment(overrider):
    overrider.add_assignment(Assignment(value=10, path=[PathComponent(component=10, indexed_cls=list)]))

    with pytest.raises(FailedToDeepAssignException):
        overrider.override([])


@pytest.mark.regression
def test_overrider_doesnt_raise_exception_when_out_of_bounds_on_non_active_assignment(overrider):
    overrider.add_assignment(Assignment(value=10, path=[PathComponent(component=10, indexed_cls=list)]))
    # we create another assignment to make the previous not the active assignment
    overrider.add_assignment(Assignment(value=0, path=[]))

    # We only truly want to make sure the above assignment didn't cause an exception
    new_data = overrider.override([])

    assert new_data == 0


def test_overrider_keeps_order(overrider):
    overrider.add_assignment(Assignment(value=[5], path=[]))
    overrider.add_assignment(Assignment.create_default([PathComponent(component=0, indexed_cls=list)]))
    overrider.add_assignment(Assignment(value=[10], path=[]))

    # We only truly want to make sure the above assignment didn't cause an exception
    new_data = overrider.override([20])

    assert new_data == [10]


def test_overrider_loads_default_assignment_from_text():
    overrider = Overrider()
    overrider.load_from_assignment_text(assignment_text='quib[2] = default')
    assert overrider[0] == Assignment.create_default([PathComponent(None, 2)])


def test_overrider_wont_add_default_assignment_when_empty():
    overrider = Overrider()
    overrider.add_assignment(Assignment.create_default([]))
    assert len(overrider) == 0

