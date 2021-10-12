import numpy as np
from pytest import fixture

from pyquibbler.quib.assignment import Overrider, Assignment
from pyquibbler.quib.assignment.assignment import PathComponent


@fixture
def overrider():
    return Overrider()


def test_overrider_add_assignment_and_override(overrider):
    overrider.add_assignment(Assignment(value=0, path=[PathComponent(indexed_cls=np.ndarray, component=0)]))
    new_data = overrider.override([1])

    assert new_data == [0]


def test_overrider_with_global_override(overrider):
    overrider.add_assignment(Assignment(value=[2, 3, 4], path=[PathComponent(indexed_cls=list, component=...)]))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [2, 3, 4]


def test_overrider_with_global_override_and_partial_assignments(overrider):
    overrider.add_assignment(Assignment(value=[2, 3, 4], path=[PathComponent(indexed_cls=list, component=...)]))
    overrider.add_assignment(Assignment(value=100, path=[PathComponent(indexed_cls=list, component=0)]))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [100, 3, 4]


def test_overrider_with_field_assignment(overrider):
    dtype = [('name', np.unicode, 21), ('age', np.int_)]
    overrider.add_assignment(Assignment(value=1, path=[PathComponent(indexed_cls=np.ndarray, component='age')]))
    new_data = overrider.override(np.array([('maor2', 23)], dtype=dtype))

    assert new_data['age'] == 1


def test_overrider_with_field_assignment_and_indices(overrider):
    dtype = [('name', np.unicode, 21), ('age', np.int_)]
    overrider.add_assignment(Assignment(value=1, path=[PathComponent(indexed_cls=np.ndarray,
                                                                     component=(0, 0)),
                                                       PathComponent(indexed_cls=np.ndarray,
                                                                     component="age")
                                                       ]))
    new_data = overrider.override(np.array([[('maor2', 23)]], dtype=dtype))

    assert np.array_equal(new_data, np.array([[('maor2', 1)]], dtype=dtype))


def test_overrider_remove_assignment(overrider):
    overrider.add_assignment(Assignment(value=[1, 1], path=[PathComponent(component=..., indexed_cls=list)]))
    overrider.remove_assignment([PathComponent(component=1, indexed_cls=list)])
    new_data = overrider.override([0, 0])

    assert new_data == [1, 0]
