import numpy as np

# Note that tests per specific types of inversal are in translation/
# As a general rule- any specific scenario of a translation should be a test there, and any checking of surrounding
# should be here
import pytest

from pyquibbler import iquib, q
from pyquibbler.quib.quib import Quib


def test_quib_inverse_getitem(create_quib_with_return_value):
    quib = create_quib_with_return_value([1, 2, 3], allow_overriding=True)
    child = quib[0]

    child.assign(10)

    assert quib.get_value() == [10, 2, 3]


@pytest.fixture()
def basic_dtype():
    return [('name', '|S21'), ('age', 'i4')]


def test_inverse_assign_field_array_with_function_and_fancy_indexing_and_field_name(basic_dtype,
                                                                                    create_quib_with_return_value):
    arr = create_quib_with_return_value(np.array([[('shlomi', 9)], [('maor', 3)]], dtype=basic_dtype),
                                        allow_overriding=True, lazy=False)
    rotation_quib = np.rot90(arr)

    first_value: Quib = rotation_quib[[0], [1]]

    first_value.assign("heisenberg", 'name')

    assert np.array_equal(arr.get_value(), np.array([[("shlomi", 9)], [("heisenberg", 3)]], dtype=basic_dtype))


def test_inverse_assign_nested_with_fancy_rot90_fancy_and_replace(create_quib_with_return_value):
    dtype = [('name', '|S10'), ('nested', [('child_name', np.compat.unicode, 30)], (3,))]
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

    dumbest_child.assign(new_name, ...)

    assert np.array_equal(families.get_value(), np.array([[(name_1, first_children)],
                                                          [(name_2, [*second_children[:-1], new_name])]], dtype=dtype))


@pytest.mark.regression
def test_inverse_setitem_on_non_ndarray_after_rotation(create_quib_with_return_value):
    first_quib_arg = create_quib_with_return_value([[[1, 2, 3]]], allow_overriding=True)
    rotated: Quib = np.rot90(first_quib_arg[0])

    rotated.assign(4, (0, 0))

    assert np.array_equal(first_quib_arg.get_value(), [[[1, 2, 4]]])


@pytest.mark.regression
def test_assignment_to_list_after_np_function(create_quib_with_return_value):
    first_quib_arg = create_quib_with_return_value([[1, 2, 3]], allow_overriding=True)
    rotated: Quib = np.rot90(first_quib_arg)
    rotated.get_value()
    first_quib_arg[0][2] = 4.1

    assert np.array_equiv(first_quib_arg.get_value(), [[[1, 2, 4]]])


@pytest.mark.regression
def test_slice_assignment_to_list_after_get_item(create_quib_with_return_value):
    a = create_quib_with_return_value([1, 2, 3, 4], allow_overriding=True)
    b: Quib = a[:3].setp(cache_mode='on')
    b.get_value()
    a[1:] = [20, 30, 40]
    print(b.get_value())
    assert np.array_equiv(b.get_value(), [1, 20, 30])


@pytest.mark.regression
def test_assignment_to_list_make_it_unarrayable_after_np_function(create_quib_with_return_value):
    first_quib_arg = create_quib_with_return_value([[11, 12, 13], [21, 22, 23]], allow_overriding=True)
    rotated: Quib = np.rot90(first_quib_arg)
    rotated.get_value()
    del(rotated)
    first_quib_arg[0] = [41]

    assert first_quib_arg.get_value() == [[41], [21, 22, 23]]


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

    c.assign(3)

    assert np.array_equal(a.get_value(), np.array([3, 2, 3]))


def test_inversion_create_nice_looking_assignments(create_quib_with_return_value):
    a = create_quib_with_return_value(np.array([1, 2, 3]), allow_overriding=True)
    b = a[0:1]
    c = b[0]

    c.assign(3)

    assert str(a.get_override_list()) == 'quib[0] = 3'


def test_invert_elementwise_operator(create_quib_with_return_value):
    a = create_quib_with_return_value(np.array([1, 2, 3]), allow_overriding=True)
    b = create_quib_with_return_value(np.array([1, 2, 3]))
    c = a + b

    c[0] = 40

    assert a[0].get_value() == 39


def test_invert_single_arg_elementwise_with_colon_slice(create_quib_with_return_value):
    n = create_quib_with_return_value(3, allow_overriding=True)
    a = np.arange(1, n + 1).setp(allow_overriding=True)
    b = np.log2(a)

    b[:] = 3
    n.assign(4)
    assert np.array_equal(a.get_value(), [8, 8, 8, 8])


@pytest.mark.regression
def test_deep_assignment_with_object_ndarray():
    a = iquib({'name': 'maor'})
    b = np.array([a], dtype=object)
    b0 = b[0]['name']

    b0.assign('bobby')

    assert b0.get_value() == 'bobby'


@pytest.mark.regression
def test_change_minor_sources():
    a = iquib(1)
    t = iquib(10)
    b = np.array([a, t])
    b0 = b[0]

    b0.assign(5)

    assert b0.get_value() == 5


@pytest.mark.regression
def test_inverse_with_multiple_selections_and_colon():
    a = iquib(1)
    b = iquib(2)
    c = np.array([a, b, 3])
    d = c[0:2]

    d[:] = 0

    assert list(d.get_value()) == [0, 0]
    assert np.array_equal(c.get_value(), [0, 0, 3])
    assert a.get_value() == 0
    assert b.get_value() == 0


@pytest.mark.regression
def test_inverse_with_single_arg_operator():
    a = iquib(np.array([1, 2, 3]))
    b = -a
    b[1:3] = 5

    assert np.array_equal(a.get_value(), [1, -5, -5])


@pytest.mark.regression
def test_inverse_tile_scalar():
    a = iquib(7)
    b = np.tile(a, 3)
    b[1] = 5

    assert a.get_value() == 5


@pytest.mark.regression
def test_inverse_tile_array():
    a = iquib([7])
    b = np.tile(a, 3)
    b[1] = 5

    assert a.get_value() == [5]


@pytest.mark.parametrize(
    ['func', 'initial_input', 'assigned_value', 'expected_new_input'], [
        (str, 4, '55', 55),
        (str, 4.0, '55', 55.),
        (str, 4.0, '5.5', 5.5),
        (str, np.int32(2), '7', np.int32(7)),
        (str, [1, 3, 4.2], '["hi", 5]', ["hi", 5]),
        (str, np.array([1, 2, 3]), '[11, 12, 13]', np.array([11, 12, 13])),
        (int, 4.3, 10, 10.),
        (int, 4.3, 10.3, 10.),
        (int, np.array([[4.3]]), 10.3, np.array([[10.]])),
        (int, '15', 10.2, '10'),
        (bool, 2, False, 0),
        (bool, 2, True, 1),
        (bool, 2., True, 1.),
        (bool, np.array([2.]), False, np.array([0.])),
        (bool, np.array([[2]]), True, np.array([[1]])),
    ]
)
def test_inverse_casting(func, initial_input, assigned_value, expected_new_input):
    input = iquib(initial_input)
    output = q(func, input)
    output.assign(assigned_value)

    input_value = input.get_value()
    print(input_value)
    assert np.array_equal(input_value, expected_new_input) and type(input_value) == type(expected_new_input)
    if isinstance(input_value, np.ndarray):
        assert input_value.dtype == expected_new_input.dtype


def test_invert_array_with_quib_elements(create_quib_with_return_value):
    a = create_quib_with_return_value(1, allow_overriding=True)
    b = create_quib_with_return_value(2, allow_overriding=True)
    ab = np.array([a, b])
    ab[:] = 0

    assert np.array_equal(ab.get_value(), np.array([0, 0]))


def test_inverse_operator():
    a = iquib(20)
    b = 100 - a
    assert b.get_value() == 80, "sanity"
    b.assign(70)
    assert b.get_value() == 70
    assert a.get_value() == 30


def test_list_addition_inversal():
    a = iquib([0, 1, 2])
    b = iquib([3, 4])
    ab = a + b

    assert ab.get_value() == [0, 1, 2, 3, 4]
    ab[1] = 11

    assert a.get_value() == [0, 11, 2]
    assert ab.get_value() == [0, 11, 2, 3, 4]


def test_deep_assign_into_array():
    a0 = iquib({'name': 'roy'})
    a1 = iquib({'name': 'maor'})
    b = np.array([a0, a1])
    assert b.get_value()[0]['name'] == 'roy'

    b[0]['name'] = 'kishony'
    assert a0.get_value()['name'] == 'kishony'


def test_inverse_element_wise_of_list_of_quibs():
    a = iquib(1)
    b = iquib(2)

    c = np.exp2([0, a, b])
    c[1] = 8

    assert a.get_value() == 3
