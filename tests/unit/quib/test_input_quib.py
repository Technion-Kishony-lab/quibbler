from unittest.mock import Mock
from pytest import fixture

from pyquibbler import iquib
from pyquibbler.quib import DefaultFunctionQuib


@fixture
def input_quib_val():
    return [1]


@fixture
def input_quib(input_quib_val):
    return iquib(input_quib_val)


def create_child_with_valid_cache(input_quib):
    child = DefaultFunctionQuib.create(Mock())
    child.get_value()
    assert child.is_cache_valid
    input_quib.add_child(child)
    return child


def test_input_quib_setitem(input_quib):
    child1 = create_child_with_valid_cache(input_quib)
    child2 = create_child_with_valid_cache(input_quib)

    # Mutate the input quib so its children will be invalidated and redrawn
    input_quib[0] = 'new_val!!'

    assert not child1.is_cache_valid
    assert not child2.is_cache_valid


def test_input_quib_get_value(input_quib, input_quib_val):
    assert input_quib.get_value() == input_quib_val
