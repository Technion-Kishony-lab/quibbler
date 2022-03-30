from unittest import mock

import pytest

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException, UnknownEnumException
from pyquibbler.quib.func_calling.cache_mode import CacheMode
from pyquibbler.quib.exceptions import InvalidCacheBehaviorForQuibException
from pyquibbler.quib.factory import create_quib


def test_quib_set_cache_behaviour_forces_correct_type(quib):
    with pytest.raises(InvalidArgumentTypeException):
        quib.cache_mode = 1


def test_quib_setp(quib):
    quib.setp(cache_mode='off')

    assert quib.cache_mode == CacheMode.OFF


def test_quib_setp_with_invalid_cache_mode(quib):
    with pytest.raises(UnknownEnumException):
        quib.setp(cache_mode='ondfdd')


@pytest.fixture()
def random_quib():
    func = mock.Mock()
    add_definition_for_function(func=func, function_definition=FuncDefinition(is_random=True))
    return create_quib(func=func)


def test_can_set_quib_cache_mode_to_on_when_random(random_quib):
    random_quib.ache_behavior = CacheMode.ON


def test_quib_cache_mode_on_by_default_when_is_random(random_quib):
    assert random_quib.cache_mode == CacheMode.ON
