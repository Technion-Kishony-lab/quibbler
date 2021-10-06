from unittest import mock

import numpy as np
from operator import getitem

import pytest

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.reverse_assignment import reverse_function_quib


def reverse(func, indices, value, args, kwargs=None):
    reverse_function_quib(function_quib=DefaultFunctionQuib.create(
        func=func,
        func_args=args,
        func_kwargs=kwargs
    ), assignment=Assignment(value=value, paths=[indices]))


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

    b.assign(Assignment(value=[3, 4], paths=[True]))

    assert np.array_equal(a.get_value(), [3, 4, 2])


def test_reverse_assign_pyobject_array():
    a = iquib(np.array([mock.Mock()]))
    new_mock = mock.Mock()
    b = a[0]

    b.assign(Assignment(value=new_mock, paths=[...]))

    assert a.get_value() == [new_mock]


@pytest.mark.regression
def test_reverse_assign_to_single_element():
    a = iquib(np.array([0, 1, 2]))
    b = a[1]

    b.assign(Assignment(value=3, paths=[...]))

    assert np.array_equal(a.get_value(), [0, 3, 2])


def test_reverse_assign_repeat():
    q = iquib(3)
    repeated = np.repeat(q, 4)

    repeated.assign(Assignment(value=10, paths=[2]))

    assert q.get_value() == 10


def test_reverse_assign_full():
    q = iquib(3)
    repeated = np.full((1, 3), q)

    repeated.assign(Assignment(value=10, paths=[[[0], [1]]]))

    assert q.get_value() == 10


@pytest.fixture()
def basic_dtype():
    return [('name', '|S21'), ('age', 'i4')]


def test_reverse_assign_field_array(basic_dtype):
    a = iquib(np.array([[("maor", 24)], [("maor2", 22)]], dtype=basic_dtype))
    b = a[[1], [0]]

    b.assign(Assignment(value=23, paths=['age']))

    assert np.array_equal(a.get_value(), np.array([[("maor", 24)], [("maor2", 23)]], dtype=basic_dtype))
    assert np.array_equal(b.get_value(), np.array([('maor2', 23)], dtype=basic_dtype))


def test_reverse_assign_field_array_with_function_and_fancy_indexing_and_field_name(basic_dtype):
    arr = iquib(np.array([[('shlomi', 9)], [('maor', 3)]],  dtype=basic_dtype))
    rotation_quib = DefaultFunctionQuib.create(func=np.rot90, func_args=(arr,))
    first_value = rotation_quib[[0], [1]]

    first_value.assign(Assignment(value="heisenberg", paths=['name']))

    assert np.array_equal(arr.get_value(), np.array([[("shlomi", 9)], [("heisenberg", 3)]], dtype=basic_dtype))


def test_reverse_assign_field_with_multiple_field_values(basic_dtype):
    name_1 = 'heisenberg'
    name_2 = 'john'
    arr = iquib(np.array([[('', 9)], [('', 3)]],  dtype=basic_dtype))
    arr.assign(Assignment(value=[[name_1], [name_2]], paths=['name']))

    assert np.array_equal(arr.get_value(), np.array([[(name_1, 9)], [(name_2, 3)]], dtype=basic_dtype))


def test_reverse_assign_nested_with_fancy_rot90_fancy_and_replace():
    dtype = [('name', '|S10'), ('nested', [('child_name', np.unicode, 30)], (3,))]
    name_1 = 'Maor'
    name_2 = 'StupidMan'
    first_children = ['Yechiel', "Yossiel", "Yirmiyahu"]
    second_children = ["Dumb", "Dumber", "Wow..."]
    new_name = "HOWDUMBBBB"
    families = iquib(np.array([[(name_1, first_children)],
                               [(name_2, second_children)]], dtype=dtype))
    second_family = families[([1], [0])]  # Fancy Indexing, should copy
    children_names = second_family['nested']['child_name']
    rotated_children = DefaultFunctionQuib.create(func=np.rot90, func_args=(children_names,))

    dumbest_child = rotated_children[([0], [0])]
    dumbest_child.assign(Assignment(value=new_name, paths=[...]))

    assert np.array_equal(families.get_value(), np.array([[(name_1, first_children)],
                                                          [(name_2, [*second_children[:-1], new_name])]], dtype=dtype))


@pytest.mark.regression
def test_reverse_setitem_on_non_ndarray():
    first_quib_arg = iquib([[1, 2, 3]])
    first_row = first_quib_arg[0]

    first_row.assign(Assignment(value=10, paths=[0]))

    assert np.array_equal(first_quib_arg.get_value(), [[10, 2, 3]])


@pytest.mark.regression
def test_reverse_setitem_on_non_ndarray_after_rotation():
    first_quib_arg = iquib([[[1, 2, 3]]])
    rotated = DefaultFunctionQuib.create(func=np.rot90, func_args=(first_quib_arg[0],))

    rotated.assign(Assignment(value=4, paths=[(0, 0)]))

    assert np.array_equal(first_quib_arg.get_value(), [[[1, 2, 4]]])
