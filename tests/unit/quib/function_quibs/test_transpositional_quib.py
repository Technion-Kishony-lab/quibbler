from operator import getitem

import numpy as np
import pytest

from pyquibbler import iquib, Assignment
from pyquibbler.quib.function_quibs.transpositional_quib import TranspositionalQuib


@pytest.fixture()
def input_quib():
    return iquib(np.array([[1, 2, 3]]))


@pytest.fixture()
def rot90_quib(input_quib):
    return TranspositionalQuib.create(
        func=np.rot90,
        func_args=(input_quib,)
    )


@pytest.fixture()
def getitem_quib(rot90_quib):
    getitem_quib_ = TranspositionalQuib.create(
        func=getitem,
        func_args=(rot90_quib, (0, 0))
    )
    getitem_quib_.get_value()
    return getitem_quib_


def test_invalidate_and_redraw_invalidates_that_which_should_be_invalidated(rot90_quib, getitem_quib):
    rot90_quib.invalidate_and_redraw(path=[(0, 0)])

    assert not getitem_quib.is_cache_valid


def test_invalidate_and_redraw_does_not_invalidate_that_which_should_not_be_invalidated(rot90_quib, getitem_quib):
    rot90_quib.invalidate_and_redraw(path=[(1, 0)])

    assert getitem_quib.is_cache_valid


def test_invalidate_and_redraw_invalidates_that_which_should_be_invalidated_with_multiple_steps(
        input_quib,
        getitem_quib
):
    input_quib.invalidate_and_redraw(path=[(0, 1)])

    assert getitem_quib.is_cache_valid


def test_invalidate_and_redraw_does_not_invalidate_that_which_should_be_invalidated_with_multiple_steps(
        input_quib,
        getitem_quib
):
    input_quib.invalidate_and_redraw(path=[(0, 2)])

    assert not getitem_quib.is_cache_valid


def test_invalidate_and_redraw_on_dict(
):
    quib = iquib({"maor": 1})
    second_quib = quib["maor"]

    quib.invalidate_and_redraw(path=["maor"])

    assert not second_quib.is_cache_valid


def test_invalidate_and_redraw_on_dict2(
):
    quib = iquib({"maor": 1, 'y': 2})
    second_quib = quib["maor"]

    quib.invalidate_and_redraw(path=[PathComponent("y")])

    assert second_quib.is_cache_valid


def test_invalidate_and_redraw_on_dict_after_index(
):
    quib = iquib([1, 2, {
        'MAOR': 'YELED EFES'
    }])
    second_quib = quib[2]
    third_quib = second_quib['MAOR']

    quib.invalidate_and_redraw(path=[2])

    assert not third_quib.is_cache_valid
