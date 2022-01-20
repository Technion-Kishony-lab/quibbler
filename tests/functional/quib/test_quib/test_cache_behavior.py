from unittest import mock

import pytest

from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.utilities.input_validation_utils import InvalidArgumentException
from pyquibbler.quib.func_calling.cache_behavior import CacheBehavior, UnknownCacheBehaviorException
from pyquibbler.quib.exceptions import InvalidCacheBehaviorForQuibException
from pyquibbler.quib.factory import create_quib


def test_quib_set_cache_behaviour_forces_correct_type(quib):
    with pytest.raises(InvalidArgumentException):
        quib.set_cache_behavior(1)


def test_quib_setp(quib):
    quib.setp(cache_behavior='off')

    assert quib.get_cache_behavior() == CacheBehavior.OFF


def test_quib_setp_with_invalid_cache_behavior(quib):
    with pytest.raises(UnknownCacheBehaviorException):
        quib.setp(cache_behavior='ondfdd')


@pytest.fixture()
def random_quib():
    func = mock.Mock()
    add_definition_for_function(func=func, function_definition=FuncDefinition(is_random_func=True))
    return create_quib(func=func)


def test_can_set_quib_cache_behavior_to_on_when_random(random_quib):
    random_quib.set_cache_behavior(CacheBehavior.ON)


@pytest.mark.parametrize(
    'cache_behavior',
    filter(lambda cache_behavior: cache_behavior is not CacheBehavior.ON, CacheBehavior)
)
def test_cant_set_quib_cache_behavior_to_something_other_than_on_when_random(random_quib, cache_behavior):
    with pytest.raises(InvalidCacheBehaviorForQuibException):
        random_quib.set_cache_behavior(cache_behavior)


def test_quib_cache_behavior_on_by_default_when_is_random(random_quib):
    assert random_quib.get_cache_behavior() is CacheBehavior.ON
