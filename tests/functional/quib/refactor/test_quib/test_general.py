import operator
import unittest.mock
from unittest import mock

import numpy as np
import pytest

from pyquibbler.input_validation_utils import InvalidArgumentException
from pyquibbler.quib.refactor.factory import create_quib


def test_quib_get_shape():
    arr = np.array([1, 2, 3])
    quib = create_quib(mock.Mock(return_value=arr))

    assert quib.get_shape() == arr.shape


def test_quib_iter_first(quib):
    quib.func.return_value = [1, 2, 3]
    first, second = quib.iter_first()

    assert (first.get_value(), second.get_value()) == tuple(quib.func.return_value[:2])


def test_quib_getitem(quib):
    quib.func.return_value = [1, 2, 3]

    getitem_quib = quib[0]

    assert getitem_quib.func == operator.getitem
    assert getitem_quib.get_value() == quib.func.return_value[0]


def test_quib_get_type(quib):
    assert quib.get_type() == list


def test_quib_configure(quib):
    quib = quib.setp(allow_overriding=True, name="pasten")

    assert quib.name == 'pasten'
    assert quib.allow_overriding is True


def test_quib_configure_with_invalid_value(quib):
    with pytest.raises(InvalidArgumentException):
        quib.setp(allow_overriding=3, name="pasten")


def test_quib_knows_it_is_created_in_a_context():
    def func():
        assert create_quib(mock.Mock(return_value=0)).created_in_get_value_context
        return 'yay'

    assert create_quib(func).get_value() == 'yay'
