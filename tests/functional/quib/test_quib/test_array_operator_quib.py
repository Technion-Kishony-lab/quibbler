import numpy as np
import pytest

from pyquibbler import iquib, Quib
from pyquibbler.quib.exceptions import QuibsShouldPrecedeException


def test_add_array_and_quib():
    w = iquib(10)
    a = np.array([1, 2, 3])
    wa = w + a
    assert isinstance(wa, Quib),  "sanity"
    with pytest.raises(QuibsShouldPrecedeException, match='.*'):
        aw = a + w
