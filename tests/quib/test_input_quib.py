from unittest.mock import Mock

from pytest import fixture

from pyquibbler import iquib
from pyquibbler.quib import Quib, DefaultFunctionQuib


@fixture
def input_quib_val():
    return [1]


@fixture
def input_quib(input_quib_val):
    return iquib(input_quib_val)


def create_child_with_valid_cache(input_quib, artist_redrawer):
    child = DefaultFunctionQuib.create(Mock())
    child.add_artists_redrawer(artist_redrawer)
    child.get_value()
    assert child.is_cache_valid
    input_quib.add_child(child)
    return child


def test_input_quib_getitem(input_quib, input_quib_val):
    got = input_quib[0]
    assert isinstance(got, Quib)
    assert got.get_value() == input_quib_val[0]


def test_input_quib_setitem(input_quib):
    artist_redrawer_mock = Mock()
    child1 = create_child_with_valid_cache(input_quib, artist_redrawer_mock)
    child2 = create_child_with_valid_cache(input_quib, artist_redrawer_mock)
    # Mutate the input quib so its children will be invalidated and redrawn
    input_quib[0] = 'new_val!!'
    assert artist_redrawer_mock.redraw.call_count == 1
    assert not child1.is_cache_valid
    assert not child2.is_cache_valid


def test_input_quib_get_value(input_quib, input_quib_val):
    assert input_quib.get_value() == input_quib_val
