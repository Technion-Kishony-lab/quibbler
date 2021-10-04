from pytest import fixture

from pyquibbler.quib.assignment import Overrider, Assignment


@fixture
def overrider():
    return Overrider()


def test_overrider_add_assignment_and_override(overrider):
    overrider.add_assignment(Assignment(key=0, value=0))
    new_data = overrider.override([1])

    assert new_data == [0]


def test_overrider_with_global_override(overrider):
    overrider.add_assignment(Assignment(key=None, value=[2, 3, 4]))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [2, 3, 4]


def test_overrider_with_global_override_and_partial_assignments(overrider):
    overrider.add_assignment(Assignment(key=None, value=[2, 3, 4]))
    overrider.add_assignment(Assignment(key=0, value=100))
    new_data = overrider.override([1, 2, 3])

    assert new_data == [100, 3, 4]
