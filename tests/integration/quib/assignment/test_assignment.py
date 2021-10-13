import numpy as np

from pyquibbler import iquib


def test_getitem_setitem_with_slicing_and_fancy_indexing_inverses_and_overrides_correctly():
    q = iquib(np.array([[1, 2, 3], [4, 5, 6]]))

    getitemed = q[np.array([0, 0, 1, 1]), np.array([0, 2, 0, 2])]
    getitemed[0:3] = np.array([200, 300, 400])

    assert np.array_equal(q.get_value(), np.array([[200, 2, 300], [400, 5, 6]]))