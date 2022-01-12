import os
import pathlib
from unittest import mock

import numpy as np
import pytest

from pyquibbler.refactor.env import GET_VARIABLE_NAMES
from pyquibbler.refactor.quib.exceptions import CannotSaveAsTextException
from pyquibbler.refactor.quib.specialized_functions.iquib import iquib, CannotNestQuibInIQuibException


def test_iquib_get_value_returns_argument():
    quib = iquib(3)

    assert quib.get_value() == 3


def test_iquib_is_overridable():
    quib = iquib(3)

    quib.assign_value(10)

    assert quib.get_value() == 10


@pytest.mark.get_variable_names(True)
def test_iquib_pretty_repr():
    quib = iquib(10)

    assert quib.pretty_repr() == "quib = iquib(10)"


def test_iquib_cannot_have_quibs():
    quib = iquib(10)

    with pytest.raises(CannotNestQuibInIQuibException):
        iquib(quib)


def test_iquib_repr_doesnt_fail():
    repr(iquib([10]))


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_iquib_pretty_repr_str():
    a = iquib('a')

    assert a.pretty_repr() == 'a = iquib(\'a\')'

# File system
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


@pytest.mark.parametrize("obj", [
    np.array([1, 2, 3]),
    [1, 2, 3],
    {"a": "b"},
    (1, 2, 3),
])
def test_save_txt_and_load_iquib_ndarray(obj, tmpdir):
    a = iquib(obj)
    a.assign_value(obj)

    a.save_if_relevant()
    a.load()

    files = os.listdir(f"{tmpdir}/input_quibs")
    assert len(files) == 1
    assert files[0].endswith('.txt')
    assert np.array_equal(a.get_value(), obj)


class A:
    pass


def test_save_saves_not_as_txt_if_cant(tmpdir):

    a = iquib(np.array([mock.Mock()]))
    a.assign_value_to_key(key=0, value=A())

    a.save_if_relevant()

    quib_files = os.listdir(f"{tmpdir}/input_quibs")
    assert len(quib_files) == 1
    assert quib_files[0].endswith(".quib")


def test_save_iquib_with_save_path(tmpdir):
    with GET_VARIABLE_NAMES.temporary_set(True):
        a = iquib(10)
    a.assign_value(11)
    path = pathlib.Path(tmpdir.strpath) / "whatever"
    a.set_save_directory(path)

    a.save_if_relevant()
    a.load()

    assert os.path.exists(path)
    assert a.get_value() == 11


