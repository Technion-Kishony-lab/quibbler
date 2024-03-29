from unittest import mock

import pytest

from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException, InvalidArgumentValueException
from pyquibbler.quib.factory import create_quib


@pytest.mark.get_variable_names(True)
def test_quib_var_name():
    my_quib = create_quib(func=mock.Mock())
    assert my_quib.name == "my_quib"


@pytest.mark.get_variable_names(True)
def test_quib_var_name_after_setp():
    my_quib = create_quib(func=mock.Mock()).setp()
    assert my_quib.name == "my_quib"


@pytest.mark.get_variable_names(True)
def test_quib_var_name_after_setp_without_variable():
    my_quib = create_quib(func=mock.Mock())
    my_quib.setp()
    assert my_quib.name == "my_quib"


def test_quib_with_valid_set_name():
    my_quib = create_quib(func=mock.Mock())
    name = "hello_quib"

    my_quib.name = name

    assert my_quib.name == name


def test_quib_with_invalid_set_name():
    my_quib = create_quib(func=mock.Mock(return_value=1))
    name = "hello quib!"
    with pytest.raises(InvalidArgumentValueException, match='.*'):
        my_quib.name = name


@pytest.mark.get_variable_names(True)
def test_quib_with_multiple_in_same_line():
    a, b = create_quib(func=mock.Mock(return_value=1)), create_quib(func=mock.Mock(return_value=2))

    assert a.name == 'a'
    assert b.name == 'b'


@pytest.mark.get_variable_names(True)
def test_quib_doesnt_get_name_if_it_is_created_in_context():
    def func():
        noname = create_quib(mock.Mock(return_value=0))
        assert noname.assigned_name is None

    create_quib(func).get_value()


def test_quib_cannot_assign_int_to_name(quib):
    with pytest.raises(InvalidArgumentTypeException, match='.*'):
        quib.name = 1


@pytest.mark.get_variable_names(True)
def test_quib_can_assign_none_to_name():
    a = create_quib(mock.Mock(return_value=["val"]))
    assert a.assigned_name == 'a', "Sanity check"

    a.name = None

    assert a.assigned_name is None
