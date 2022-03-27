from unittest import mock

import pytest

from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException
from pyquibbler.quib.factory import create_quib


@pytest.mark.get_variable_names(True)
def test_quib_var_name():
    my_quib = create_quib(func=mock.Mock())
    assert my_quib.props.name == "my_quib"


@pytest.mark.get_variable_names(True)
def test_quib_var_name_after_setp():
    my_quib = create_quib(func=mock.Mock()).setp()
    assert my_quib.props.name == "my_quib"


@pytest.mark.get_variable_names(True)
def test_quib_var_name_after_setp_without_variable():
    my_quib = create_quib(func=mock.Mock())
    my_quib.setp()
    assert my_quib.props.name == "my_quib"


def test_quib_with_valid_set_name():
    my_quib = create_quib(func=mock.Mock())
    name = "hello_quib"

    my_quib.props.name = name

    assert my_quib.props.assigned_name == name


def test_quib_with_invalid_set_name():
    my_quib = create_quib(func=mock.Mock(return_value=1))
    name = "hello quib!"

    try:
        my_quib.props.name = name
    except ValueError:
        pass
    else:
        assert False


@pytest.mark.get_variable_names(True)
def test_quib_with_multiple_in_same_line():
    a, b = create_quib(func=mock.Mock(return_value=1)), create_quib(func=mock.Mock(return_value=2))

    assert a.props.name == 'a'
    assert b.props.name == 'b'


@pytest.mark.get_variable_names(True)
def test_quib_doesnt_get_name_if_it_is_created_in_context():
    def func():
        noname = create_quib(mock.Mock(return_value=0))
        assert noname.props.assigned_name is None

    create_quib(func).get_value()


def test_quib_cannot_assign_int_to_name(quib):
    with pytest.raises(InvalidArgumentTypeException):
        quib.props.name = 1


@pytest.mark.get_variable_names(True)
def test_quib_can_assign_none_to_name():
    a = create_quib(mock.Mock(return_value=["val"]))
    assert a.props.name == 'a', "Sanity check"

    a.props.name = None

    assert a.props.assigned_name is None
