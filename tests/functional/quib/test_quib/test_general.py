import operator
from unittest import mock

import numpy as np
import pytest

from pyquibbler import Quib
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException
from pyquibbler.quib.factory import create_quib


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
    with pytest.raises(InvalidArgumentTypeException):
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


def test_parents(create_quib_with_return_value):
    grandparent = create_quib_with_return_value(2)
    parent1 = create_quib_with_return_value(1)
    parent2 = create_quib(func=mock.Mock(), args=(grandparent,))
    me = create_quib(func=mock.Mock(), args=(0, parent1, 2), kwargs=dict(a=parent2, b=3))

    assert me.get_parents() == {parent1, parent2}


def test_quib_ancestors(create_quib_with_return_value):
    great_grandparent = create_quib_with_return_value(1)
    grandparent = create_quib(func=mock.Mock(), args=(great_grandparent,))
    parent = create_quib(func=mock.Mock(), args=(grandparent,))
    me = create_quib(func=mock.Mock(), args=(parent,))

    assert me.get_ancestors() == {great_grandparent, grandparent, parent}


def test_quib_named_parents(create_quib_with_return_value):
    grandma = create_quib(func=mock.Mock(), assigned_name='grandma')
    mom = create_quib(func=mock.Mock(), args=(grandma,), assigned_name='mom')
    grandpa = create_quib(func=mock.Mock(), assigned_name='grandpa')
    dad = create_quib(func=mock.Mock(), args=(grandpa,), assigned_name=None)  # unnamed
    me = create_quib(func=mock.Mock(), args=(mom, dad))

    assert me.get_parents(True) == {mom, grandpa}


def test_quib_named_children(create_quib_with_return_value):
    me = create_quib(func=mock.Mock())
    son = create_quib(func=mock.Mock(), args=(me,), assigned_name=None)  # unnamed
    daughter = create_quib(func=mock.Mock(), args=(me,), assigned_name='daughter')
    grand_son = create_quib(func=mock.Mock(), args=(son,), assigned_name='grandson')
    grand_daughter = create_quib(func=mock.Mock(), args=(daughter,), assigned_name='grandpa')

    assert me.get_children(True) == {daughter, grand_son}

