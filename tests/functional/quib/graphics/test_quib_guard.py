import pytest

from pyquibbler import iquib
from pyquibbler.quib.quib_guard import QuibGuard, CannotAccessQuibInScopeException, \
    AnotherQuibGuardIsAlreadyActiveException


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


def test_quib_guard_within_quib_guard_gives_last_quib_guard_and_raises():
    quib = iquib(3)
    with QuibGuard({quib}):
        with QuibGuard(set()):
            with pytest.raises(CannotAccessQuibInScopeException):
                quib.get_value()


def test_quib_guard_within_quib_guard_gives_last_quib_guard_and_does_not_raise():
    quib = iquib(3)
    with QuibGuard(set()):
        with QuibGuard({quib}):
            # sanity, make sure we don't raise exception
            assert quib.get_value() == 3


def test_quib_guard_within_quib_guard_exits_and_goes_back_to_previous_quib_guard():
    quib = iquib(3)
    with QuibGuard({quib}):
        with QuibGuard(set()):
            pass
        # sanity, make sure we don't raise exception
        assert quib.get_value() == 3
