import numpy as np
import pytest

from pyquibbler import iquib


@pytest.fixture
def a():
    return iquib(1, assigned_name='a')


@pytest.fixture
def b(a):
    return a + 2


@pytest.fixture
def c(b):
    return b + 3


def test_quiby_name_repr(a):
    a_name = a.get_quiby_name()
    assert a_name.name == 'get_quiby_name(a)'


def test_quiby_name_value_is_name_of_parent(a):
    a_name = a.get_quiby_name()
    assert a_name.get_value() == 'a'


def test_quiby_name_value_is_repr_of_parent(a):
    a_name = a.get_quiby_name(as_repr=True)
    assert a_name.get_value() == 'a = iquib(1)'


def test_quiby_name_as_repr_can_be_a_quib(a):
    as_repr = iquib(False)
    a_name = a.get_quiby_name(as_repr=as_repr)
    assert a_name.get_value() == 'a'
    as_repr.assign(True)
    assert a_name.get_value() == 'a = iquib(1)'


def test_quiby_name_invalidates_when_parent_name_changes(a):
    a_name = a.get_quiby_name().setp(cache_mode='on')
    assert a_name.get_value() == 'a'
    assert a_name.handler.quib_function_call._result_metadata is not None
    a.assigned_name = 'new_a'
    assert a_name.handler.quib_function_call._result_metadata is None
    assert a_name.get_value() == 'new_a'


def test_quiby_name_invalidates_when_grand_grand_parent_name_changes(a, c):
    c_name = c.get_quiby_name()
    assert c_name.get_value() == 'a + 2 + 3'
    assert c_name.handler.quib_function_call._result_metadata is not None
    a.assigned_name = 'new_a'
    assert c_name.handler.quib_function_call._result_metadata is None
    assert c_name.get_value() == 'new_a + 2 + 3'


def test_quiby_name_does_not_invalidates_when_parent_value_changes(a):
    a_name = a.get_quiby_name()
    assert a_name.get_value() == 'a'
    assert a_name.handler.quib_function_call._result_metadata is not None
    a.assign(17)
    assert a_name.handler.quib_function_call._result_metadata is not None
