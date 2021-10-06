from unittest import mock

import numpy as np
from operator import getitem

import pytest
from pytest import mark

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.assignment import IndicesAssignment, Assignment
from pyquibbler.quib.assignment.reverse_assignment import reverse_function_quib


def reverse(func, indices, value, args, kwargs=None):
    reverse_function_quib(function_quib=DefaultFunctionQuib.create(
        func=func,
        func_args=args,
        func_kwargs=kwargs
    ), assignment=IndicesAssignment(value=value, indices=indices, field=None))


def test_reverse_rot90():
    quib_arg = iquib(np.array([[1, 2, 3]]))
    new_value = 200

    reverse(func=np.rot90, args=(quib_arg,), value=np.array([new_value]), indices=[0])

    assert np.array_equal(quib_arg.get_value(), np.array([[1, 2, new_value]]))


def test_reverse_concat():
    first_quib_arg = iquib(np.array([[1, 2, 3]]))
    second_quib_arg = iquib(np.array([[8, 12, 14]]))
    new_value = 20

    reverse(func=np.concatenate, args=((first_quib_arg, second_quib_arg),), indices=(0, 0),
            value=np.array([new_value]))

    assert np.array_equal(first_quib_arg.get_value(), np.array([[new_value, 2, 3]]))
    assert np.array_equal(second_quib_arg.get_value(), np.array([[8, 12, 14]]))


def test_reverse_concat_in_both_arguments():
    first_quib_arg = iquib(np.array([[1, 2, 3]]))
    second_quib_arg = iquib(np.array([[8, 12, 14]]))
    first_new_value = 200
    second_new_value = 300

    reverse(func=np.concatenate, args=((first_quib_arg, second_quib_arg),), indices=([0, 1], [0, 0]),
            value=np.array([first_new_value, second_new_value]))

    assert np.array_equal(first_quib_arg.get_value(), np.array([[first_new_value, 2, 3]]))
    assert np.array_equal(second_quib_arg.get_value(), np.array([[second_new_value, 12, 14]]))


def test_reverse_getitem():
    quib_arg = iquib(np.array([[1, 2, 3], [4, 5, 6]]))

    reverse(func=getitem, args=(quib_arg, 1), indices=0,
            value=100)

    assert np.array_equal(quib_arg.get_value(), np.array([[1, 2, 3], [100, 5, 6]]))


def test_reverse_assign_to_sub_array():
    a = iquib(np.array([0, 1, 2]))
    b = a[:2]

    b.assign(Assignment(value=[3, 4], field=None))

    assert np.array_equal(a.get_value(), [3, 4, 2])


def test_reverse_assign_pyobject_array():
    a = iquib(np.array([mock.Mock()]))
    new_mock = mock.Mock()
    b = a[0]

    b.assign(Assignment(value=new_mock, field=None))

    assert a.get_value() == [new_mock]


@pytest.mark.regression
def test_reverse_assign_to_single_element():
    a = iquib(np.array([0, 1, 2]))
    b = a[1]

    b.assign(Assignment(value=3, field=None))

    assert np.array_equal(a.get_value(), [0, 3, 2])


def test_reverse_assign_field_array():
    dtype = [('name', np.unicode, 21), ('age', np.int_)]
    a = iquib(np.array([[("maor", 24)], [("maor2", 22)]], dtype=dtype))
    b = a[[1], [0]]

    b.assign(Assignment(value=23, field='age'))

    assert np.array_equal(a.get_value(), np.array([[("maor", 24)], [("maor2", 23)]], dtype=dtype))
    assert np.array_equal(b.get_value(), np.array([('maor2', 23)], dtype=dtype))


def test_reverse_assign_repeat():
    q = iquib(3)
    repeated = np.repeat(q, 4)

    repeated.assign(IndicesAssignment(value=10, indices=2))

    assert q.get_value() == 10


def test_reverse_assign_full():
    q = iquib(3)
    repeated = np.full((1, 3), q)

    repeated.assign(IndicesAssignment(value=10, indices=[[0], [1]]))

    assert q.get_value() == 10
