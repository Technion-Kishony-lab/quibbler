from unittest import mock

import numpy as np
import pytest

from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException
from pyquibbler.assignment import InvalidTypeException, BoundAssignmentTemplate, RangeAssignmentTemplate
from pyquibbler.path.data_accessing import FailedToDeepAssignException
from pyquibbler.quib.exceptions import OverridingNotAllowedException
from pyquibbler.quib.factory import create_quib
from tests.functional.utils import slicer, get_mock_with_repr


def test_quib_must_assign_bool_to_overriding(quib):
    with pytest.raises(InvalidArgumentTypeException):
        quib.allow_overriding = 1


def test_quib_fails_when_not_matching_assignment_template():
    quib = create_quib(mock.Mock(return_value=[1, 2, 3]), allow_overriding=True)
    quib.set_assignment_template(1, 3)
    quib.assign("hello johnny", 2)

    with pytest.raises(InvalidTypeException):
        quib.get_value()


@pytest.mark.parametrize(['args', 'expected_template'], [
    ((BoundAssignmentTemplate(2, 4),), BoundAssignmentTemplate(2, 4)),
    ((1, 2), BoundAssignmentTemplate(1, 2)),
    ((1, 2, 3), RangeAssignmentTemplate(1, 2, 3))
])
def test_set_and_get_assignment_template(args, expected_template, quib):
    quib.set_assignment_template(*args)
    template = quib.assignment_template

    assert template == expected_template


@pytest.mark.parametrize('args', [(), (1, 2, 3, 4)])
def test_set_assignment_template_with_wrong_number_of_args_raises_typeerror(args, quib):
    with pytest.raises(TypeError):
        quib.set_assignment_template(*args)


def test_set_assignment_template_with_range(quib):
    quib.set_assignment_template(1, 2, 3)
    template = quib.assignment_template

    assert template == RangeAssignmentTemplate(1, 2, 3)


# TODO: should following override tests be in a separate place? (hint: they should)

def test_quib_override_without_assignment_template():
    mock_func = mock.Mock()
    mock_func.return_value = ['old item']
    quib = create_quib(func=mock_func, allow_overriding=True)
    new_item = 'new item'
    quib[0] = new_item

    assert quib.get_value()[0] is new_item


def test_quib_override_with_assignment_template():
    mock_assignment_template = mock.Mock(spec=BoundAssignmentTemplate)
    mock_assignment_template.convert.return_value = "something that wont change on deepcopy"
    quib = create_quib(func=mock.Mock(return_value=['oh no']), allow_overriding=True)
    quib.set_assignment_template(mock_assignment_template)
    quib[0] = 'val'

    result = quib[0].get_value()

    mock_assignment_template.convert.assert_called_with('val')
    assert result == mock_assignment_template.convert.return_value


def test_overrides_are_applied_in_order():
    quib = create_quib(mock.Mock(return_value=[2]), allow_overriding=True)
    quib[0] = 1
    quib[0] = -1

    assert quib[0].get_value() == -1


def test_quib_get_override_list_shows_user_friendly_information_about_overrides():
    quib = create_quib(func=mock.Mock(return_value=["1"]), allow_overriding=True)
    key_repr = 'key_repr'
    value_repr = 'value_repr'
    key_mock = get_mock_with_repr(key_repr)
    value_mock = get_mock_with_repr(value_repr)
    quib[key_mock] = value_mock

    overrides_repr = repr(quib.get_override_list())

    assert key_repr in overrides_repr
    assert value_repr in overrides_repr


@pytest.mark.parametrize(['data', 'overrides', 'expected_mask'], [
    ([], [], []),
    ([0], [], [False]),
    ([0], [(0, 1)], [True]),
    ([0, 1], [], [False, False]),
    ([0, 1], [(1, 2)], [False, True]),
    ([[0, 1], [2, 3]], [(1, [4, 5])], [[False, False], [True, True]]),
    ([[0, 1], [2, 3]], [((0, 0), 5)], [[True, False], [False, False]]),
    ([[0, 1], [2, 3]], [(slicer[:], 5)], [[True, True], [True, True]]),
])
def test_quib_get_override_mask(data, overrides, expected_mask):
    quib = create_quib(func=mock.Mock(return_value=np.array(data)), allow_overriding=True)
    for key, value in overrides:
        quib[key] = value
    assert np.array_equal(quib.get_override_mask().get_value(), expected_mask)


def test_quib_get_override_mask_whole_array_override():
    quib = create_quib(func=mock.Mock(return_value=np.array([0, 1])), allow_overriding=True)
    quib.assign(np.array([0, 1, 2]))
    assert np.array_equal(quib.get_override_mask().get_value(), [True, True, True])


def test_quib_override_when_overriding_not_allowed(quib):
    override = mock.Mock()

    with pytest.raises(OverridingNotAllowedException) as exc_info:
        quib.handler.override(override, allow_overriding_from_now_on=False)

    assert exc_info.value.quib is quib
    assert exc_info.value.override is override
    assert isinstance(str(exc_info.value), str)


@pytest.mark.regression
def test_quib_get_override_mask_with_list():
    quib = create_quib(func=mock.Mock(return_value=[10, [21, 22], 30]), allow_overriding=True)
    quib[1][1] = 222

    mask = quib.get_override_mask()

    assert mask.get_value() == [False, [False, True], False]


@pytest.mark.regression
def test_quib_get_override_mask_dict():
    quib = create_quib(func=mock.Mock(return_value={'city': 'Haifa', 'beach': 'yes'}), allow_overriding=True)
    quib['city'] = 'Tel-Aviv'

    mask = quib.get_override_mask()

    assert mask.get_value() == {'city': True, 'beach': False}


def test_quib_does_not_fail_when_assignment_fails_on_second_get_value():
    quib = create_quib(mock.Mock(return_value=[1, 2, 3]), allow_overriding=True)
    quib.assign(1, 2)
    quib.get_value()
    quib.assign([1])

    # just make sure we don't fail
    quib.get_value()


def test_quib_fails_when_given_invalid_assignment_on_first_get_value():
    quib = create_quib(mock.Mock(return_value=[1, 2, 3]), allow_overriding=True)
    quib.assign(1, 4)

    with pytest.raises(FailedToDeepAssignException):
        quib.get_value()


def test_full_overriding_prevents_get_value():
    a = create_quib(mock.Mock(return_value=[1, 2, 3]), allow_overriding=True)
    a.assign([11, 12, 13, 14])

    a3 = a[3]

    assert a3.get_value() == 14
