import numpy as np
import pytest

from pyquibbler import iquib
from pyquibbler.quib.assignment import PathComponent
from pyquibbler.quib.assignment.assignment import get_hashable_path


def test_getitem_setitem_with_slicing_and_fancy_indexing_inverses_and_overrides_correctly():
    q = iquib(np.array([[1, 2, 3], [4, 5, 6]]))

    getitemed = q[np.array([0, 0, 1, 1]), np.array([0, 2, 0, 2])]
    getitemed[0:3] = np.array([200, 300, 400])

    assert np.array_equal(q.get_value(), np.array([[200, 2, 300], [400, 5, 6]]))


@pytest.mark.parametrize("components_in_path", [
    [slice(None, None,  None)],
    [np.array([1, 2, 3]), np.array([1, 2, 3])],
    [(np.array([1, 2, 3]), np.array([1, 2, 3]))],
    [np.array([1, 2, 3])],
    [([slice(None, None,  None)],)],
])
def test_hash_path(components_in_path):
    path = [PathComponent(component=c, indexed_cls=object) for c in components_in_path]

    # Make sure we don't raise an exception
    hash(get_hashable_path(path))
