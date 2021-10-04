from operator import getitem

import numpy as np

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.assignment.reverse_assignment import reverse_function_quib


def reverse(func, indices, value, args, kwargs=None):
    reverse_function_quib(function_quib=DefaultFunctionQuib.create(
        func=func,
        func_args=args,
        func_kwargs=kwargs
    ), value=value, indices=indices, )


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

    b.assign([3, 4])

    assert np.array_equal(a.get_value(), [3, 4, 2])
