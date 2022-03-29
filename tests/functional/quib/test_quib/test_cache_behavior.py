from unittest import mock

import pytest

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException, UnknownEnumException
from pyquibbler.quib.func_calling.caching_options import CachingOptions
from pyquibbler.quib.factory import create_quib


def test_quib_set_cache_behaviour_forces_correct_type(quib):
    with pytest.raises(InvalidArgumentTypeException):
        quib.props.caching = 1


def test_quib_setp(quib):
    quib.setp(caching='off')

    assert quib.props.caching == CachingOptions.OFF


def test_quib_setp_with_invalid_cache_behavior(quib):
    with pytest.raises(UnknownEnumException):
        quib.setp(caching='ondfdd')


@pytest.fixture()
def random_quib():
    func = mock.Mock()
    add_definition_for_function(func=func, function_definition=FuncDefinition(is_random_func=True))
    return create_quib(func=func)


def test_can_set_quib_cache_behavior_to_on_when_random(random_quib):
    random_quib.ache_behavior = CachingOptions.ON


def test_quib_cache_behavior_on_by_default_when_is_random(random_quib):
    assert random_quib.props.caching == CachingOptions.ON

