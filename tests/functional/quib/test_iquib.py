import os
import pathlib
from unittest import mock

import numpy as np
import pytest

from pyquibbler.env import GET_VARIABLE_NAMES
from pyquibbler.quib.exceptions import CannotSaveValueAsTextException, CannotSaveAssignmentsAsTextException
from pyquibbler.quib.specialized_functions.iquib import iquib, CannotNestQuibInIQuibException
from pyquibbler.file_syncing.types import SaveFormat
from pyquibbler.quib import Quib

def test_iquib_get_value_returns_argument():
    quib = iquib(3)

    assert quib.get_value() == 3


def test_iquib_is_overridable():
    quib = iquib(3)

    quib.assign(10)

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
@pytest.mark.parametrize(['save_format'], [
    (SaveFormat.TXT,),
    (SaveFormat.BIN,),
    (SaveFormat.VALUE_TXT,),
    (SaveFormat.VALUE_BIN,),
])
def test_iquib_save_and_load(save_format: SaveFormat):
    save_name = "example_quib"
    original_value = [1, 2, 3]
    a = iquib(original_value).setp(save_format=save_format, name=save_name)
    a.assign(10, 1)
    a.save()

    b = iquib(original_value).setp(save_format=save_format, name=save_name)
    b.load()

    assert a.get_value() == b.get_value()


@pytest.mark.get_variable_names(True)
def test_iquib_loads_if_same_name():
    save_name = "example_quib"
    original_value = [1, 2, 3]
    a = iquib(original_value)
    a.name = save_name
    a.assign(10, 1)

    a.save()
    # the name "example_quib" is critical here! it must be the same as save_name for the quib to actually load
    example_quib = iquib(original_value)
    example_quib.load()

    assert a.get_value() == example_quib.get_value()


def test_iquib_does_not_save_if_irrelevant(project):
    a = iquib(1)
    b: Quib = (a + 1).setp(assigned_name='b')
    b.save()

    assert len(os.listdir(project.directory)) == 0


@pytest.mark.parametrize("obj", [
    np.array([1, 2, 3]),
    [1, 2, 3],
    {"a": "b"},
    (1, 2, 3),
])
@pytest.mark.get_variable_names(True)
def test_save_txt_and_load_iquib_ndarray(obj, tmpdir):
    a = iquib(obj).setp(save_format=SaveFormat.VALUE_TXT)
    a.assign(obj)

    a.save()
    a.load()

    files = os.listdir(f"{tmpdir}")
    assert len(files) == 1
    assert files[0].endswith('.txt')
    assert np.array_equal(a.get_value(), obj)


class A:
    pass


def test_save_raises_exception_when_cannot_save_as_text(tmpdir):

    a = iquib(np.array([mock.Mock()])).setp(save_format=SaveFormat.TXT, name='my_quib')
    a.assign(A(), 0)

    try:
        a.save()
    except CannotSaveAssignmentsAsTextException:
        quib_files = os.listdir(f"{tmpdir}")
        assert len(quib_files) == 0
        return

    assert False


def test_save_iquib_with_save_path(tmpdir):
    with GET_VARIABLE_NAMES.temporary_set(True):
        a = iquib(10)
    a.assign(11)
    path = pathlib.Path(tmpdir.strpath) / "whatever"
    a.save_directory = path

    a.save()
    a.load()

    assert os.path.exists(path)
    assert a.get_value() == 11


