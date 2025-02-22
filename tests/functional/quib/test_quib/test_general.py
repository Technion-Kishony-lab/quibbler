import operator
from unittest import mock

import numpy as np
import pytest

from pyquibbler import Quib
from pyquibbler.env import ITER_RAISE_EXCEPTION
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException
from pyquibbler.quib.factory import create_quib


def test_quib_get_shape():
    arr = np.array([1, 2, 3])
    quib = create_quib(mock.Mock(return_value=arr))

    assert quib.get_shape() == arr.shape


def test_quib_get_ndim():
    arr = np.array([1, 2, 3])
    quib = create_quib(mock.Mock(return_value=arr))

    assert quib.get_ndim() == 1


def test_quib_iter_first(quib):
    quib.func.return_value = [1, 2, 3]
    first, second = quib.iter_first()

    assert (first.get_value(), second.get_value()) == tuple(quib.func.return_value[:2])


def test_quib_iter(quib):
    quib.func.return_value = [1, 2, 3]
    first, second = quib

    assert (first.get_value(), second.get_value()) == tuple(quib.func.return_value[:2])


def test_quib_iter_exception(quib):
    quib.func.return_value = [1, 2, 3]
    with ITER_RAISE_EXCEPTION.temporary_set(True):
        with pytest.raises(TypeError):
            first, second = quib


def test_quib_getitem(quib):
    quib.func.return_value = [1, 2, 3]

    getitem_quib: Quib = quib[0]

    assert getitem_quib.func == operator.getitem
    assert getitem_quib.get_value() == quib.func.return_value[0]


def test_quib_get_type(quib):
    assert quib.get_type() == list


def test_quib_configure(quib):
    quib = quib.setp(allow_overriding=True, name="pasten")

    assert quib.name == 'pasten'
    assert quib.allow_overriding is True


def test_quib_configure_with_invalid_value(quib):
    with pytest.raises(InvalidArgumentTypeException, match='.*'):
        quib.setp(allow_overriding=3, name="pasten")


def test_quib_knows_it_is_created_in_a_context():
    def func():
        assert create_quib(mock.Mock(return_value=0)).handler.created_in_get_value_context
        return 'yay'

    assert create_quib(func).get_value() == 'yay'


def test_cant_mutate_function_quib_args_after_creation():
    args = [[], 'cool']
    kwargs = dict(a=[])
    function_quib = create_quib(func=mock.Mock(), args=args, kwargs=kwargs)
    args[0].append(1)
    args.append(1)
    kwargs['b'] = 1
    kwargs['a'].append(1)

    function_quib.get_value()

    function_quib.func.assert_called_once_with([], 'cool', a=[])


