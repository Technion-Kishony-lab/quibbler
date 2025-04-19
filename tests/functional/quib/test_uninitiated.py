import pytest

from pyquibbler import iquib, quiby, q, is_quiby, Quib
from pyquibbler.function_overriding.is_initiated import IS_QUIBBLER_INITIATED


def test_iquib_does_not_create_quib_when_uninitiated():
    with IS_QUIBBLER_INITIATED.temporary_set(False):
        with pytest.warns(UserWarning):
            quib = iquib(3)
        assert not isinstance(quib, Quib) and quib == 3
    quib = iquib(3)
    assert isinstance(quib, Quib) and quib.get_value() == 3, "sanity"


def test_quiby_does_not_create_quiby_func_when_uninitiated():
    with IS_QUIBBLER_INITIATED.temporary_set(False):
        with pytest.warns(UserWarning):
            quiby_str = quiby(str)
        with pytest.warns(UserWarning):
            assert not is_quiby(quiby_str)
    quiby_str = quiby(str)
    assert is_quiby(quiby_str), "sanity"


def test_q_does_not_create_quib_when_uninitiated():
    with IS_QUIBBLER_INITIATED.temporary_set(False):
        with pytest.warns(UserWarning):
            quib = q(str, 3)
        assert not isinstance(quib, Quib) and quib == '3'
    quib = q(str, 3)
    assert isinstance(quib, Quib) and quib.get_value() == '3'
