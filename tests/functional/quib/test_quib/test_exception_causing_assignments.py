import weakref

import pytest

from developer_tools.deep_get_referrers import deep_get_referrers
from pyquibbler import iquib, quiby, Project


# @pytest.mark.skip
def test_prevent_assignments_causing_exception():
    @quiby(is_graphics=True)
    def validate_input(x):
        if x < 0:
            raise Exception("x cannot be negative")

    a = iquib(1)
    validate = validate_input(a)

    a.assign(-1)
    assert a.get_value() == 1

    val_ref = weakref.ref(validate)
    del validate
    assert val_ref() is None

    a_ref = weakref.ref(a)
    del a
    assert a_ref() is None

