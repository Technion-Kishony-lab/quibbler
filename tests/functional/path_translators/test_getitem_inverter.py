from dataclasses import dataclass
from operator import getitem
from typing import Any
from unittest import mock

import numpy as np
import pytest

from pyquibbler import Assignment
from pyquibbler.translation.types import Source
from pyquibbler.quib import PathComponent
from pyquibbler.quib.refactor.quib import Quib
from tests.functional.translation.utils import inverse


@dataclass
class GetItemTestCase:
    name: str
    source_value: Any
    item: Any
    set_indices: Any
    set_value: Any
    expected: Any


def inverse_getitem(a, b, indices, value, empty_path: bool = False):
    return inverse(func=getitem, args=(a, b), indices=indices, value=value, empty_path=empty_path)


@pytest.mark.parametrize("getitem_test_case", [
    GetItemTestCase(
        name="simple",
        source_value=np.array([[1, 2, 3], [4, 5, 6]]),
        item=1,
        set_indices=0,
        set_value=100,
        expected=np.array([[1, 2, 3], [100, 5, 6]])
    ),
    GetItemTestCase(
        name="sub array",
        source_value=np.array([0, 1, 2]),
        item=slice(None, 2, None),
        set_indices=True,
        set_value=[3, 4],
        expected=[3, 4, 2]
    ),
    GetItemTestCase(
        name="non view slice",
        source_value=np.array([0, 1, 2]),
        item=[0, 2],
        set_indices=0,
        set_value=3,
        expected=[3, 1, 2]
    ),
])
def test_inverse(getitem_test_case):
    source = Source(getitem_test_case.source_value)

    sources_to_results = inverse_getitem(source, getitem_test_case.item, indices=getitem_test_case.set_indices,
                                         value=getitem_test_case.set_value)

    assert np.array_equal(sources_to_results[source], getitem_test_case.expected)


def test_inverse_assign_pyobject_array():
    a = Source(np.array([mock.Mock()]))
    new_mock = mock.Mock()

    sources_to_result = inverse_getitem(a, 0, empty_path=True, indices=None, value=new_mock)

    assert sources_to_result[a] == [new_mock]


@pytest.mark.regression
def test_inverse_assign_to_single_element():
    a = Source(np.array([0, 1, 2]))

    sources_to_result = inverse_getitem(a, 1, empty_path=True, indices=None, value=3)

    assert np.array_equal(sources_to_result[a], [0, 3, 2])


@pytest.fixture()
def basic_dtype():
    return [('name', '|S21'), ('age', 'i4')]


def test_inverse_assign_field_array(basic_dtype):
    a = Source(np.array([[("maor", 24)], [("maor2", 22)]], dtype=basic_dtype))

    sources_to_result = inverse_getitem(a, ([1], [0]), indices="age", value=23)

    assert np.array_equal(sources_to_result[a], np.array([[("maor", 24)], [("maor2", 23)]], dtype=basic_dtype))


@pytest.mark.regression
def test_inverse_getitem_on_non_ndarray():
    source = Source([[1, 2, 3]])

    sources_to_result = inverse_getitem(source, 0, indices=0, value=10)

    assert np.array_equal(sources_to_result[source], [[10, 2, 3]])


@pytest.mark.regression
def test_inverse_with_resulting_int_and_changing_value_shape():
    a = Source(np.arange(6).reshape(2, 3))

    sources_to_result = inverse_getitem(a, (slice(None, None, None), slice(None, None, None)),
                                        indices=(slice(None, None, None), slice(None, None, None)), value=0)

    assert np.array_equal(sources_to_result[a], np.full((2, 3), fill_value=0))
