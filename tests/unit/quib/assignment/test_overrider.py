from unittest import mock
from unittest.mock import Mock

import pytest
from pytest import fixture

from pyquibbler.quib.assignment import Overrider, Assignment
from pyquibbler.quib.assignment.overrider import MixBetweenGlobalAndPartialOverridesException


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

    overrider.override_collection(data_mock)

    new_assignment_mock.apply.assert_called_once_with(data_mock, None)


def test_overrider_override(overrider, assignment_mock, data_mock, assignment_template_mock):
    overrider.override_collection(data_mock, assignment_template_mock)

    assignment_mock.apply.assert_called_once_with(data_mock, assignment_template_mock)


def test_overrider_is_global_override_when_true():
    overrider = Overrider(assignments=[
        Assignment(
            key=None,
            value=None
        )
    ])

    assert overrider.is_global_override() is True


def test_overrider_is_global_override_when_false():
    overrider = Overrider(assignments=[
        Assignment(
            key=1,
            value=None
        )
    ])

    assert overrider.is_global_override() is False


def test_overrider_get_global_override():
    value = mock.Mock()
    overrider = Overrider(assignments=[
        Assignment(
            key=None,
            value=value
        )
    ])

    assert overrider.get_global_override() is value


def test_get_global_override_raises_exception_when_mixed_partial_and_global_overiding():
    overrider = Overrider(assignments=[
        Assignment(
            key=None,
            value=0
        ),
        Assignment(
            key=1,
            value=0
        )
    ])

    with pytest.raises(MixBetweenGlobalAndPartialOverridesException):
        overrider.get_global_override()


def test_override_collection_raises_exception_when_mixed_partial_and_global_overiding():
    overrider = Overrider(assignments=[
        Assignment(
            key=1,
            value=0
        ),
        Assignment(
            key=None,
            value=0
        ),
    ])

    with pytest.raises(MixBetweenGlobalAndPartialOverridesException):
        overrider.override_collection({})
