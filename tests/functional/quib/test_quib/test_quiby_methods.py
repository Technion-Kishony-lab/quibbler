import numpy as np

from pyquibbler import iquib
from pytest import fixture


@fixture
def array_value():
    return np.array(np.arange(6).reshape((2, 3)))


@fixture
def quib(array_value):
    a = iquib(array_value, assigned_name='a')
    return a


@fixture
def quib_sum(quib):
    return quib.sum(axis=0)


@fixture
def quib_flatten(quib):
    return quib.flatten()


def test_call_method_get_value(quib, quib_sum):
    assert np.array_equal(quib.get_value().sum(axis=0), quib_sum.get_value())


def test_call_method_inverse(quib, quib_flatten):
    quib_flatten[4] = 10
    print(quib.get_value())
    assert np.array_equal(quib.get_value(), np.array([0, 1, 2, 3, 10, 5]).reshape((2, 3)))


def test_call_method_invalidate(quib, quib_sum):
    quib_sum.get_value()
    quib[0, 1] = 10
    assert np.array_equal(quib_sum.handler.quib_function_call.cache._invalid_mask, [False, True, False])


def test_call_method_repr(quib, quib_sum):
    assert repr(quib_sum) == 'a.sum(axis=0)'


def test_tolist_method_get_value(quib, array_value):
    tolist = quib.tolist()
    assert tolist.get_value() == array_value.tolist()


def test_tolist_method_invalidation(quib):
    tolist = quib.tolist()
    tolist.get_value()
    assert np.array_equal(tolist.handler.quib_function_call.cache._invalid_mask, [False, False]), "sanity"
    quib[0, 1] = 10
    assert np.array_equal(tolist.handler.quib_function_call.cache._invalid_mask, [True, False])


def test_tolist_method_inversion(quib):
    tolist = quib.tolist()
    tolist[0][1] = 10
    assert np.array_equal(quib.get_value(), [[0, 10, 2], [3, 4, 5]])
