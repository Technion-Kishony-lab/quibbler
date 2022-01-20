import numpy as np

# Note that tests per specific types of inversal are in translation/
# As a general rule- any specific scenario of a translation should be a test there, and any checking of surrounding
# should be here
import pytest

from pyquibbler.quib.quib import Quib


def test_quib_inverse_getitem(create_quib_with_return_value):
    quib = create_quib_with_return_value([1, 2, 3], allow_overriding=True)
    child = quib[0]

    child.assign_value(10)

    assert quib.get_value() == [10, 2, 3]


@pytest.fixture()
def basic_dtype():
    return [('name', '|S21'), ('age', 'i4')]


def test_inverse_assign_field_array_with_function_and_fancy_indexing_and_field_name(basic_dtype,
                                                                                    create_quib_with_return_value):
    arr = create_quib_with_return_value(np.array([[('shlomi', 9)], [('maor', 3)]], dtype=basic_dtype),
                                        allow_overriding=True, evaluate_now=True)
    rotation_quib = np.rot90(arr)

    first_value: Quib = rotation_quib[[0], [1]]

    first_value.assign_value_to_key(value="heisenberg", key='name')

    assert np.array_equal(arr.get_value(), np.array([[("shlomi", 9)], [("heisenberg", 3)]], dtype=basic_dtype))


def test_inverse_assign_nested_with_fancy_rot90_fancy_and_replace(create_quib_with_return_value):
    dtype = [('name', '|S10'), ('nested', [('child_name', np.unicode, 30)], (3,))]
    name_1 = 'Maor'
    name_2 = 'StupidMan'
    first_children = ['Yechiel', "Yossiel", "Yirmiyahu"]
    second_children = ["Dumb", "Dumber", "Wow..."]
    new_name = "HOWDUMBBBB"
    families = create_quib_with_return_value(np.array([[(name_1, first_children)],
                                                       [(name_2, second_children)]], dtype=dtype),
                                             allow_overriding=True)
    second_family = families[([1], [0])]  # Fancy Indexing, should copy
    children_names = second_family['nested']['child_name']
    rotated_children = np.rot90(children_names)
    dumbest_child: Quib = rotated_children[([0], [0])]

    dumbest_child.assign_value_to_key(value=new_name, key=...)

    assert np.array_equal(families.get_value(), np.array([[(name_1, first_children)],
                                                          [(name_2, [*second_children[:-1], new_name])]], dtype=dtype))


@pytest.mark.regression
def test_inverse_setitem_on_non_ndarray_after_rotation(create_quib_with_return_value):
    first_quib_arg = create_quib_with_return_value([[[1, 2, 3]]], allow_overriding=True)
    rotated: Quib = np.rot90(first_quib_arg[0])

    rotated.assign_value_to_key(value=4, key=(0, 0))

    assert np.array_equal(first_quib_arg.get_value(), [[[1, 2, 4]]])


def test_inverse_getitem_on_dict_and_rot90(create_quib_with_return_value):
    quib = create_quib_with_return_value({'a': [[1, 2, 3]]}, allow_overriding=True)
    get_item = quib['a']
    rot90 = np.rot90(get_item)

    rot90[(0, 0)] = 20

    assert np.array_equal(quib['a'].get_value(), [[1, 2, 20]])


def test_inverse_with_int_as_result_of_function_quib_after_slicing(create_quib_with_return_value):
    a = create_quib_with_return_value(np.array([1, 2, 3]), allow_overriding=True)
    b = a[0:1]
    c = b[0]

    c.assign_value(3)

    assert np.array_equal(a.get_value(), np.array([3, 2, 3]))


def test_invert_elementwise_operator(create_quib_with_return_value):
    a = create_quib_with_return_value(np.array([1, 2, 3]), allow_overriding=True)
    b = create_quib_with_return_value(np.array([1, 2, 3]))
    c = a + b

    c[0] = 40

    assert a[0].get_value() == 39

