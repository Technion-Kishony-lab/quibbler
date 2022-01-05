import pytest

from pyquibbler.refactor.quib.specialized_functions.iquib import iquib, CannotNestQuibInIQuibException


def test_iquib_get_value_returns_argument():
    quib = iquib(3)

    assert quib.get_value() == 3


def test_iquib_is_overridable():
    quib = iquib(3)

    quib.assign_value(10)

    assert quib.get_value() == 10


@pytest.mark.get_variable_names(True)
def test_iquib_pretty_repr():
    quib = iquib(10)

    assert quib.pretty_repr() == "quib = iquib(10)"


def test_iquib_cannot_have_quibs():
    quib = iquib(10)

    with pytest.raises(CannotNestQuibInIQuibException):
        iquib(quib)


def test_iquib_repr_doesnt_fail():
    repr(iquib([10]))


@pytest.mark.regression
@pytest.mark.get_variable_names(True)
def test_iquib_pretty_repr_str():
    a = iquib('a')

    assert a.pretty_repr() == 'a = iquib(\'a\')'



