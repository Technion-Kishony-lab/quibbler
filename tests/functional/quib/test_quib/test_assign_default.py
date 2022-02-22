import numpy as np

import pytest

from pyquibbler import iquib, q, default
from pyquibbler.quib.quib import Quib


def test_quib_assign_default(create_quib_with_return_value):
    a = create_quib_with_return_value(np.array([1, 2, 3]), allow_overriding=False)
    b = (a + 10).setp(allow_overriding=True)

    b.assign(0, 1)
    assert np.array_equal(b.get_value(), [11, 0, 13]), "sanity"
    b.assign(default)
    assert np.array_equal(b.get_value(), [11, 12, 13])


@pytest.mark.parametrize(['item', 'value', 'expected_before_removal', 'item_removal', 'expected_after_removal'], [
    (1, 0, [11, 0, 13], 0, [11, 0, 13]),
    (1, 0, [11, 0, 13], 1, [11, 12, 13]),
    (1, 0, [11, 0, 13], slice(0, 2), [11, 12, 13]),
    (2, 0, [11, 12, 0], slice(0, 2), [11, 12, 0]),
])
def test_quib_setitem_default(create_quib_with_return_value, item, value, expected_before_removal,
                              item_removal, expected_after_removal):
    a = create_quib_with_return_value(np.array([1, 2, 3]), allow_overriding=False)
    b = (a + 10).setp(allow_overriding=True)

    b[item] = value
    assert np.array_equal(b.get_value(), expected_before_removal)

    b[item_removal] = default
    assert np.array_equal(b.get_value(), expected_after_removal)
