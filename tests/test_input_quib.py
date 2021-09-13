from unittest.mock import Mock

from pytest import fixture, mark

from pyquibbler import iquib
from pyquibbler.quib import Quib


@fixture
def input_quib_val():
    return [1]


@fixture
def input_quib(input_quib_val):
    return iquib(input_quib_val)


@fixture
def artist_mock():
    return Mock()


@fixture
def input_quib_child1(input_quib, artist_mock):
    q = input_quib + [2]
    q.add_artist(artist_mock)
    return q


@fixture
def input_quib_child2(input_quib, artist_mock):
    q = input_quib + [3]
    q.add_artist(artist_mock)
    return q


@mark.skip
def test_input_quib_getitem(input_quib, input_quib_val):
    got = input_quib[0]
    assert isinstance(got, Quib)
    assert got.get_value() == input_quib_val[0]


@mark.skip
def test_input_quib_setitem(input_quib, input_quib_child1, input_quib_child2, artist_mock):
    new_val = 'new_val!!'
    input_quib[0] = new_val
    assert artist_mock.redraw.call_count == 1
    assert not input_quib_child1.is_cache_valid
    assert not input_quib_child2.is_cache_valid


def test_input_quib_get_value(input_quib, input_quib_val):
    assert input_quib.get_value() == input_quib_val
