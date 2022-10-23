import numpy as np
import pytest

from pyquibbler.path import PathComponent, get_hashable_path


@pytest.mark.parametrize("components_in_path", [
    [slice(None, None,  None)],
    [np.array([1, 2, 3]), np.array([1, 2, 3])],
    [(np.array([1, 2, 3]), np.array([1, 2, 3]))],
    [np.array([1, 2, 3])],
    [([slice(None, None,  None)],)],
])
def test_hash_path(components_in_path):
    path = [PathComponent(c) for c in components_in_path]

    # Make sure we don't raise an exception
    hash(get_hashable_path(path))
