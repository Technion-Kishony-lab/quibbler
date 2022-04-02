import numpy as np
from pytest import mark

from pyquibbler import iquib
from pyquibbler.path import PathComponent


@mark.regression
def test_get_partial_value_of_a_list_iquib_with_boolean_indexing():
    value = [[1, 2], [3, 4]]
    a = iquib(value)

    index = np.array([[0, 1], [0, 0]], dtype=bool)
    partial_value = a.get_value_valid_at_path([PathComponent(component=index, indexed_cls=np.ndarray)])

    assert partial_value[0][1] == value[0][1]


@mark.regression
def test_array_of_iquib_list():
    value = [[1, 2], [3, 4]]
    a = iquib(value)

    index = np.array([[0, 1], [0, 0]], dtype=bool)
    b = np.array(a)
    c = b[index]

    assert c.get_value() == np.array(value)[index]
