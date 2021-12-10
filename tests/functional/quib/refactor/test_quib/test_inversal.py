import numpy as np

# Note that tests per specific types of inversal are in path_translators/
# As a general rule- any specific scenario of a translation should be a test there, and any checking of surrounding
# should be here
import pytest

from pyquibbler.quib.refactor.quib import Quib


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
                                        allow_overriding=True)
    rotation_quib = np.rot90(arr)
    first_value: Quib = rotation_quib[[0], [1]]

    first_value.assign_value_to_key(value="heisenberg", key='name')

    assert np.array_equal(arr.get_value(), np.array([[("shlomi", 9)], [("heisenberg", 3)]], dtype=basic_dtype))
