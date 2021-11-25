import os
from pathlib import Path
from unittest import mock
from unittest.mock import Mock

import numpy as np
import pytest
from pytest import fixture, mark, raises

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib
from pyquibbler.quib.function_quibs.cache.cache import CacheStatus
from pyquibbler.quib.input_quib import CannotNestQuibInIQuibException, CannotSaveAsTextException


@fixture
def input_quib_val():
    return [1]


@fixture
def input_quib(input_quib_val):
    return iquib(input_quib_val)


def create_child_with_valid_cache(input_quib):
    child = DefaultFunctionQuib.create(Mock())
    child.get_value()
    assert child.cache_status == CacheStatus.ALL_VALID
    input_quib.add_child(child)
    return child


# TODO: Why is this in inputquib test? This should have been in quib...
def test_input_quib_setitem_invalidates_children(input_quib):
    child1 = create_child_with_valid_cache(input_quib)
    child2 = create_child_with_valid_cache(input_quib)

    # Mutate the input quib so its children will be invalidated and redrawn
    input_quib[0] = 'new_val!!'

    assert child1.cache_status == CacheStatus.ALL_INVALID
    assert child2.cache_status == CacheStatus.ALL_INVALID


def test_input_quib_setitem_overrides_data(input_quib):
    val = 123123
    input_quib[0] = val

    assert input_quib[0].get_value() == val


def test_input_quib_get_value(input_quib, input_quib_val):
    assert input_quib.get_value() == input_quib_val


@mark.debug(True)
def test_cant_create_an_input_quib_that_contains_a_quib():
    obj = [[iquib(1)]]
    with raises(CannotNestQuibInIQuibException) as e:
        iquib(obj)


def test_iquib_repr_doesnt_fail():
    repr(iquib([10]))


@pytest.mark.get_variable_names(True)
def test_iquib_pretty_repr():
    a = iquib(10)

    assert a.pretty_repr() == 'a = iquib(10)'


@mark.regression
@pytest.mark.get_variable_names(True)
def test_iquib_pretty_repr_str():
    a = iquib('a')

    assert a.pretty_repr() == 'a = iquib(\'a\')'


def test_iquib_save_and_load():
    save_name = "example_quib"
    original_value = [1, 2, 3]
    a = iquib(original_value)
    a.set_name(save_name)
    a.assign_value_to_key(key=1, value=10)
    b = iquib(original_value)
    b.set_name(save_name)

    a.save_if_relevant()
    b.load()

    assert a.get_value() == b.get_value()


@pytest.mark.get_variable_names(True)
def test_iquib_loads_if_same_name():
    save_name = "example_quib"
    original_value = [1, 2, 3]
    a = iquib(original_value)
    a.set_name(save_name)
    a.assign_value_to_key(key=1, value=10)

    a.save_if_relevant()
    # the name "example_quib" is critical here! it must be the same as save_name for the quib to actually load
    example_quib = iquib(original_value)
    example_quib.load()

    assert a.get_value() == example_quib.get_value()


def test_iquib_does_not_save_if_irrelevant(project):
    a = iquib(1)
    a.save_if_relevant()

    assert len(os.listdir(project.input_quib_directory)) == 0


@mark.parametrize("obj", [
    np.array([1, 2, 3]),
    [1, 2, 3],
    {"a": "b"},
    (1, 2, 3),
])
def test_save_txt_and_load_iquib_ndarray(obj):
    a = iquib(obj)

    a.save_as_txt()
    a.load()

    assert np.array_equal(a.get_value(), obj)


def test_save_txt_raises_correct_exception_when_cannot_save():
    a = iquib(np.array([mock.Mock()]))

    with pytest.raises(CannotSaveAsTextException):
        a.save_as_txt()


def test_save_iquib_with_save_path(tmpdir):
    a = iquib(10)
    a.assign_value(11)
    path = Path(tmpdir.strpath) / "whatever"
    a.set_save_directory(path)

    a.save_if_relevant()
    a.load()

    assert os.path.exists(path)
    assert a.get_value() == 11
