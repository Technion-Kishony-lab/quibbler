import pytest
import numpy as np
from unittest import mock
from operator import getitem

from pyquibbler import iquib
from pyquibbler.quib import TranspositionalFuncQuib, CannotChangeQuibAtPathException
from pyquibbler.quib.assignment import Assignment
from pyquibbler.quib.assignment.assignment import PathComponent
from pyquibbler.quib.function_quibs.transpositional.getitem_function_quib import GetItemFuncQuib


def inverse(func, indices, value, args, kwargs=None):
    cls = func.__quib_wrapper__ if func != getitem else GetItemFuncQuib
    quib = cls.create(
        func=func,
        func_args=args,
        func_kwargs=kwargs
    )
    path = [PathComponent(indexed_cls=quib.get_type(), component=indices)]
    inversions = quib.get_inversions_for_assignment(assignment=Assignment(value=value, path=path))
    for inversion in inversions:
        inversion.apply()


def test_inverse_rot90():
    quib_arg = iquib(np.array([[1, 2, 3]]))
    new_value = 200

    inverse(func=np.rot90, args=(quib_arg,), value=np.array([new_value]), indices=[0])

    assert np.array_equal(quib_arg.get_value(), np.array([[1, 2, new_value]]))


def test_inverse_concat():
    first_quib_arg = iquib(np.array([[1, 2, 3]]))
    second_quib_arg = iquib(np.array([[8, 12, 14]]))
    new_value = 20

    inverse(func=np.concatenate, args=((first_quib_arg, second_quib_arg),), indices=(0, 0),
            value=np.array([new_value]))

    assert np.array_equal(first_quib_arg.get_value(), np.array([[new_value, 2, 3]]))
    assert np.array_equal(second_quib_arg.get_value(), np.array([[8, 12, 14]]))


@pytest.mark.regression
def test_inverse_concat_second_arg_non_quib():
    q = iquib([1])
    concat = np.concatenate([q, [0]])
    with pytest.raises(CannotChangeQuibAtPathException):
        concat[1] = 999


def test_inverse_concat_in_both_arguments():
    first_quib_arg = iquib(np.array([[1, 2, 3]]))
    second_quib_arg = iquib(np.array([[8, 12, 14]]))
    first_new_value = 200
    second_new_value = 300

    inverse(func=np.concatenate, args=((first_quib_arg, second_quib_arg),), indices=([0, 1], [0, 0]),
            value=np.array([first_new_value, second_new_value]))

    assert np.array_equal(first_quib_arg.get_value(), np.array([[first_new_value, 2, 3]]))
    assert np.array_equal(second_quib_arg.get_value(), np.array([[second_new_value, 12, 14]]))

# MAOR: BAD TEST, basically same as test_inverse_concat
@pytest.mark.regression
def test_inverse_concat_does_not_return_empty_assignments():
    first_quib_arg = iquib(np.array([[1, 2, 3]]))
    second_quib_arg = iquib(np.array([[8, 12, 14]]))
    new_value = 20

    quib = np.concatenate((first_quib_arg, second_quib_arg))
    inversions = quib.get_inversions_for_assignment(assignment=Assignment(value=np.array([new_value]),
                                                                          path=[PathComponent(component=(0, 0),
                                                                                              indexed_cls=quib.get_type())]))

    assert len(inversions) == 1
    assignment = inversions[0].assignment
    assert np.array_equal(assignment.path[0].component, (np.array([0]), np.array([0])))
    assert assignment.value == [20]


# GETITEM: DONE
def test_inverse_getitem():
    quib_arg = iquib(np.array([[1, 2, 3], [4, 5, 6]]))

    inverse(func=getitem, args=(quib_arg, 1), indices=0,
            value=100)

    assert np.array_equal(quib_arg.get_value(), np.array([[1, 2, 3], [100, 5, 6]]))


@pytest.mark.regression
def test_inverse_repeat_with_quib_as_repeat_count():
    arg_arr = np.array([1, 2, 3, 4])
    repeat_count = iquib(3)

    inverse(func=np.repeat, args=(arg_arr, repeat_count, 0),
            indices=(np.array([0]),),
            value=[120])

    assert repeat_count.get_value() == 3


@pytest.mark.regression
def test_inverse_repeat_with_quib_as_repeat_count_and_quib_as_arr():
    new_value = 120
    quib_arg_arr = iquib(np.array([1, 2, 3, 4]))
    repeat_count = iquib(3)

    inverse(func=np.repeat, args=(quib_arg_arr, repeat_count, 0),
            indices=(np.array([4]),),
            value=[new_value])

    assert repeat_count.get_value() == 3
    assert np.array_equal(quib_arg_arr.get_value(), np.array([
        1, new_value, 3, 4
    ]))


# MOVED: getitem
def test_inverse_assign_to_sub_array():
    a = iquib(np.array([0, 1, 2]))
    b = a[:2]

    b.assign(Assignment(value=[3, 4], path=[PathComponent(component=True, indexed_cls=b.get_type())]))

    assert np.array_equal(a.get_value(), [3, 4, 2])


# MOVED: getitem
def test_inverse_assign_pyobject_array():
    a = iquib(np.array([mock.Mock()]))
    new_mock = mock.Mock()
    b = a[0]

    b.assign(Assignment(value=new_mock, path=[]))

    assert a.get_value() == [new_mock]


# MOVED: getitem
@pytest.mark.regression
def test_inverse_assign_to_single_element():
    a = iquib(np.array([0, 1, 2]))
    b = a[1]

    b.assign(Assignment(value=3, path=[]))

    assert np.array_equal(a.get_value(), [0, 3, 2])


# Unneeded, already did repeat tests
def test_inverse_assign_repeat():
    q = iquib(3)
    repeated = np.repeat(q, 4)

    repeated.assign(Assignment(value=10, path=[PathComponent(repeated.get_type(), 2)]))

    assert q.get_value() == 10


def test_inverse_assign_full():
    q = iquib(3)
    repeated = np.full((1, 3), q)

    repeated.assign(Assignment(value=10, path=[PathComponent(repeated.get_type(), [[0], [1]])]))

    assert q.get_value() == 10



@pytest.fixture()
def basic_dtype():
    return [('name', '|S21'), ('age', 'i4')]


# MOVED: getitem
def test_inverse_assign_field_array(basic_dtype):
    a = iquib(np.array([[("maor", 24)], [("maor2", 22)]], dtype=basic_dtype))
    b = a[[1], [0]]

    b.assign(Assignment(value=23, path=[PathComponent(b.get_type(), 'age')]))

    assert np.array_equal(a.get_value(), np.array([[("maor", 24)], [("maor2", 23)]], dtype=basic_dtype))
    assert np.array_equal(b.get_value(), np.array([('maor2', 23)], dtype=basic_dtype))


# MOved: move to quib test
def test_inverse_assign_field_array_with_function_and_fancy_indexing_and_field_name(basic_dtype):
    arr = iquib(np.array([[('shlomi', 9)], [('maor', 3)]], dtype=basic_dtype))
    rotation_quib = TranspositionalFuncQuib.create(func=np.rot90, func_args=(arr,))
    first_value = rotation_quib[[0], [1]]

    first_value.assign(
        Assignment(value="heisenberg", path=[PathComponent(indexed_cls=arr.get_type(), component='name')]))

    assert np.array_equal(arr.get_value(), np.array([[("shlomi", 9)], [("heisenberg", 3)]], dtype=basic_dtype))


# BAD TEST: Didn't check anything...
def test_inverse_assign_field_with_multiple_field_values(basic_dtype):
    name_1 = 'heisenberg'
    name_2 = 'john'
    arr = iquib(np.array([[('', 9)], [('', 3)]], dtype=basic_dtype))
    arr.assign(
        Assignment(value=[[name_1], [name_2]], path=[PathComponent(indexed_cls=arr.get_type(), component='name')]))

    assert np.array_equal(arr.get_value(), np.array([[(name_1, 9)], [(name_2, 3)]], dtype=basic_dtype))


# MOVED: move to integration
def test_inverse_assign_nested_with_fancy_rot90_fancy_and_replace():
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
    rotated_children = TranspositionalFuncQuib.create(func=np.rot90, func_args=(children_names,))

    dumbest_child = rotated_children[([0], [0])]
    dumbest_child.assign(Assignment(value=new_name, path=[PathComponent(component=...,
                                                                        indexed_cls=dumbest_child.get_type())]))

    assert np.array_equal(families.get_value(), np.array([[(name_1, first_children)],
                                                          [(name_2, [*second_children[:-1], new_name])]], dtype=dtype))


# Moved: getitem
@pytest.mark.regression
def test_inverse_setitem_on_non_ndarray():
    first_quib_arg = iquib([[1, 2, 3]])
    first_row = first_quib_arg[0]

    first_row.assign(Assignment(value=10, path=[PathComponent(indexed_cls=first_row.get_type(), component=0)]))

    assert np.array_equal(first_quib_arg.get_value(), [[10, 2, 3]])


# MOVED: move to perhaps at quib level
@pytest.mark.regression
def test_inverse_setitem_on_non_ndarray_after_rotation():
    first_quib_arg = iquib([[[1, 2, 3]]])
    rotated = TranspositionalFuncQuib.create(func=np.rot90, func_args=(first_quib_arg[0],))

    rotated.assign(Assignment(value=4, path=[PathComponent(indexed_cls=rotated.get_type(), component=(0, 0))]))

    assert np.array_equal(first_quib_arg.get_value(), [[[1, 2, 4]]])


def test_inverse_assign_reshape():
    quib_arg = iquib(np.arange(9))

    inverse(func=np.reshape, args=(quib_arg, (3, 3)), value=10, indices=(0, 0))

    assert np.array_equal(quib_arg.get_value(), np.array([10, 1, 2, 3, 4, 5, 6, 7, 8]))


def test_inverse_assign_list_within_list():
    quib_arg = iquib(np.arange(9))

    inverse(func=np.reshape, args=(quib_arg, (3, 3)), value=10, indices=(0, 0))

    assert np.array_equal(quib_arg.get_value(), np.array([10, 1, 2, 3, 4, 5, 6, 7, 8]))


# MOVED: getitem
def test_inverse_getitem_on_non_view_slice():
    a = iquib(np.array([0, 1, 2]))

    a[[0, 2]][0] = 3

    assert np.array_equal(a.get_value(), [3, 1, 2])


# MOVED: move to quib level
def test_inverse_getitem_on_dict_and_rot90():
    quib = iquib({'a': [[1, 2, 3]]})
    get_item = quib['a']
    rot90 = np.rot90(get_item)

    rot90[(0, 0)] = 20

    assert np.array_equal(quib['a'].get_value(), [[1, 2, 20]])


# MOVED: move to quib level
def test_inverse_with_int_as_result_of_function_quib_after_slicing():
    a = iquib(np.array([1, 2, 3]))
    b = a[0:1]
    c = b[0]

    c.assign_value(3)

    assert np.array_equal(a.get_value(), np.array([3, 2, 3]))


# MOVED: getitem
@pytest.mark.regression
def test_inverse_with_resulting_int_and_changing_value_shape():
    a = iquib(np.arange(6).reshape(2, 3))
    b = a[:, :]

    b[:, :] = 0

    assert np.array_equal(a.get_value(), np.full((2, 3), fill_value=0))


def test_inverse_np_array():
    a = iquib([[1, 2, 3, 4]])
    b = np.array(a)

    b[(0, 0)] = 20

    assert a[0][0].get_value() == 20
