from unittest.mock import Mock
from pytest import fixture

from pyquibbler.quib.assignment import Overrider


@fixture
def assignment_mock():
    return Mock()


@fixture
def data_mock():
    return Mock()


@fixture
def overrider(assignment_mock):
    return Overrider([assignment_mock])


def test_overrider_add_assignment(overrider, data_mock):
    new_assignment_mock = Mock()
    overrider.add_assignment(new_assignment_mock)

    overrider.override(data_mock)

    new_assignment_mock.apply.assert_called_once_with(data_mock, None)


def test_overrider_override(overrider, assignment_mock, data_mock, assignment_template_mock):
    overrider.override(data_mock, assignment_template_mock)

    assignment_mock.apply.assert_called_once_with(data_mock, assignment_template_mock)
