import pytest

from pyquibbler import iquib
from pyquibbler.quib.graphics.quib_guard import QuibGuard, CannotAccessQuibInScopeException


def test_doesnt_allow_global_access():
    quib = iquib([49])
    with pytest.raises(CannotAccessQuibInScopeException):
        with QuibGuard(set()):
            quib[0].get_value()


def test_doesnt_allow_global_access_when_given_quibs():
    quib = iquib([49])
    other_quib = iquib([48])
    with pytest.raises(CannotAccessQuibInScopeException):
        with QuibGuard({other_quib}):
            quib[0].get_value()


def test_does_allow_children_of_allowed_quibs():
    quib = iquib([49])
    with QuibGuard({quib}):
        assert quib[0].get_value() == 49


def test_resets_quib_guard_after_user():
    quib = iquib([49])
    with QuibGuard(set()):
        pass

    # sanity, make sure doesn't raise exception
    assert quib.get_value() == [49]
