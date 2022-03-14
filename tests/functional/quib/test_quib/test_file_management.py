import pytest
import numpy as np

from pyquibbler import Quib
from pyquibbler import iquib
from pyquibbler.file_syncing.types import FileNotDefinedException, ResponseToFileNotDefined


def test_quib_wont_save_without_assigned_name(create_quib_with_return_value):
    example_quib = create_quib_with_return_value(5, allow_overriding=True)
    example_quib.assign(10)

    with pytest.raises(FileNotDefinedException):
        example_quib.save(ResponseToFileNotDefined.RAISE)


def test_sync_quibs_with_files(project):
    a = iquib(np.array([1., 2., 3.])).setp(name='a')
    b: Quib = (a + 10).setp(allow_overriding=True, name='b')
    b.assigned_quibs = {b}
    b[1] = 20
    a[2] = 30

    project.sync_quibs()

    del a, b
    a = iquib(np.array([1.2, 2., 5.])).setp(name='a')
    b: Quib = (a + 10).setp(allow_overriding=True, name='b')

    project.sync_quibs()
    assert np.array_equal(b.get_value(), [11., 20., 40.])
