from unittest.mock import Mock
from pytest import fixture, raises, mark

from pyquibbler import CacheBehavior
from pyquibbler.quib import ImpureFuncQuib, InvalidCacheBehaviorForImpureFuncQuibException


@fixture
def impure_function_quib():
    return ImpureFuncQuib.create(Mock())


def test_impure_function_quib_cache_behavior_on_by_default(impure_function_quib):
    assert impure_function_quib.get_cache_behavior() is CacheBehavior.ON


def test_can_set_impure_function_cache_behavior_to_on(impure_function_quib):
    impure_function_quib.set_cache_behavior(CacheBehavior.ON)


@mark.parametrize(
    'cache_behavior',
    filter(lambda cache_behavior: cache_behavior is not CacheBehavior.ON, CacheBehavior)
)
def test_cant_set_impure_function_cache_behavior_to_something_other_than_on(impure_function_quib, cache_behavior):
    with raises(InvalidCacheBehaviorForImpureFuncQuibException):
        impure_function_quib.set_cache_behavior(cache_behavior)
