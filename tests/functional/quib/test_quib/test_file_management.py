import os

import pytest
import numpy as np

from pyquibbler import Quib
from pyquibbler import iquib
from pyquibbler.file_syncing.types import FileNotDefinedException, ResponseToFileNotDefined


def test_quib_wont_save_without_assigned_name(create_quib_with_return_value):
    example_quib = create_quib_with_return_value(5, allow_overriding=True)
    example_quib.assign(10)

    with pytest.raises(FileNotDefinedException, match='.*'):
        example_quib.save(ResponseToFileNotDefined.RAISE)


def test_sync_quibs_with_files_project_initiation(project):
    a = iquib(np.array([1., 2., 3.])).setp(name='a')
    b: Quib = (a + 10).setp(allow_overriding=True, name='b', assigned_quibs='self')
    b[1] = 20
    a[2] = 30

    project.sync_quibs()

    # re-initiate the project:
    del a, b
    a = iquib(np.array([1., 2., 3.])).setp(name='a')
    b: Quib = (a + 10).setp(allow_overriding=True, name='b', assigned_quibs='self')

    project.sync_quibs()
    assert np.array_equal(a.get_value(), [1., 2., 30.])
    assert np.array_equal(b.get_value(), [11., 20., 40.])


def test_project_save_load_quibs(project, monkeypatch):
    a = iquib(np.array([1., 2., 3.])).setp(name='a')
    b: Quib = (a + 10).setp(allow_overriding=True, name='b', assigned_quibs='self')
    b[1] = 20
    a[2] = 30

    project.save_quibs()

    b[1] = 21
    a[2] = 31
    assert np.array_equal(a.get_value(), [1., 2., 31.]), "sanity"
    assert np.array_equal(b.get_value(), [11., 21., 41.]), "sanity"

    monkeypatch.setattr('builtins.input', lambda: "1")  # overwrite
    project.load_quibs()
    assert np.array_equal(a.get_value(), [1., 2., 30.])
    assert np.array_equal(b.get_value(), [11., 20., 40.])


def test_sync_quibs_with_files_and_then_file_change(project, monkeypatch):
    a = iquib(np.array([1., 2., 3.])).setp(name='a', save_format='txt')
    a[1] = 10

    project.sync_quibs()
    assert np.array_equal(a.get_value(), [1., 10., 3.]), 'sanity'

    os.remove(a.file_path)
    monkeypatch.setattr('builtins.input', lambda: "2")
    project.sync_quibs()

    assert np.array_equal(a.get_value(), [1., 2., 3.])


@pytest.mark.get_variable_names(True)
def test_quib_get_value_with_autoload(project):
    project.autoload_upon_first_get_value = True
    a = iquib([1, 2, 3]).setp(save_format="txt")
    a[0] = 2
    a.save()
    a = iquib([1, 2, 3], save_format="txt")

    result = a.get_value()  # Should autoload at this point

    assert result == [2, 2, 3]
