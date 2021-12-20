import operator
from unittest import mock

import numpy as np
import pytest

from pyquibbler.input_validation_utils import InvalidArgumentException
from pyquibbler.refactor.quib.factory import create_quib


def test_quib_get_shape():
    arr = np.array([1, 2, 3])
    quib = create_quib(mock.Mock(return_value=arr))

    assert quib.get_shape() == arr.shape


def test_quib_iter_first(quib):
    quib.func.return_value = [1, 2, 3]
    first, second = quib.iter_first()

    assert (first.get_value(), second.get_value()) == tuple(quib.func.return_value[:2])


# TODO: when operators are in motion
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


def test_parents(create_quib_with_return_value):
    grandparent = create_quib_with_return_value(2)
    parent1 = create_quib_with_return_value(1)
    parent2 = create_quib(func=mock.Mock(), args=(grandparent,))
    me = create_quib(func=mock.Mock(), args=(0, parent1, 2), kwargs=dict(a=parent2, b=3))

    assert me.parents == {parent1, parent2}


def test_quib_ancestors(create_quib_with_return_value):
    great_grandparent = create_quib_with_return_value(1)
    grandparent = create_quib(func=mock.Mock(), args=(great_grandparent,))
    parent = create_quib(func=mock.Mock(), args=(grandparent,))
    me = create_quib(func=mock.Mock(), args=(parent,))

    assert me.ancestors == {great_grandparent, grandparent, parent}

