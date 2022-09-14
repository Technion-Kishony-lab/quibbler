import numpy as np
import pytest

from pyquibbler import iquib, quiby_name, CacheStatus


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
    a_name = quiby_name(a)
    assert a_name.name == 'quiby_name(a)'


def test_quiby_name_value_is_name_of_parent(a):
    a_name = quiby_name(a)
    assert a_name.get_value() == 'a'


def test_quiby_name_invalidates_when_parent_name_changes(a):
    a_name = quiby_name(a).setp(cache_mode='on')
    assert a_name.get_value() == 'a'
    assert a_name.handler.quib_function_call._result_metadata is not None
    a.assigned_name = 'new_a'
    assert a_name.handler.quib_function_call._result_metadata is None
    assert a_name.get_value() == 'new_a'


def test_quiby_name_invalidates_when_grand_grand_parent_name_changes(a, c):
    c_name = quiby_name(c)
    assert c_name.get_value() == 'a + 2 + 3'
    assert c_name.handler.quib_function_call._result_metadata is not None
    a.assigned_name = 'new_a'
    assert c_name.handler.quib_function_call._result_metadata is None
    assert c_name.get_value() == 'new_a + 2 + 3'


def test_quiby_name_does_not_invalidates_when_parent_value_changes(a):
    a_name = quiby_name(a)
    assert a_name.get_value() == 'a'
    assert a_name.handler.quib_function_call._result_metadata is not None
    a.assign(17)
    assert a_name.handler.quib_function_call._result_metadata is not None
