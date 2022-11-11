import numpy as np
import pytest

from pyquibbler import iquib
from pytest import fixture

from pyquibbler.quib.specialized_functions.getattr import PyQuibblerAttributeError


@fixture
def array_value():
    return np.array([[1, 2, 3]])


@fixture
def quib(array_value):
    a = iquib(array_value, assigned_name='a')
    return a


@fixture
def quib_T(quib):
    return quib.T


def test_getattr_T_get_value(quib, quib_T):
    assert np.array_equal(quib.get_value().T, quib_T.get_value())


def test_getattr_T_inverse(quib, quib_T):
    quib_T[2, 0] = 10
    assert np.array_equal(quib.get_value(), [[1, 2, 10]])


def test_getattr_T_invalidate(quib, quib_T):
    quib_T.get_value()
    quib[0, 1] = 10
    assert np.array_equal(quib_T.handler.quib_function_call.cache._invalid_mask, [[False], [True], [False]])


def test_getattr_T_repr(quib, quib_T):
    assert repr(quib_T) == 'a.T'


def test_getattr_raises_on_wrong_attr(quib):
    with pytest.raises(PyQuibblerAttributeError, match='wrong_attr'):
        quib.wrong_attr
