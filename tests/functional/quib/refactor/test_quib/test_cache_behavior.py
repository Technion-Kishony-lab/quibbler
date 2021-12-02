import pytest

from pyquibbler.input_validation_utils import InvalidArgumentException
from pyquibbler.quib.refactor.cache_behavior import CacheBehavior


def test_quib_set_cache_behaviour_forces_correct_type(quib):
    with pytest.raises(InvalidArgumentException):
        quib.set_cache_behavior(1)


def test_quib_config(quib):
    quib.setp(cache_behavior='on')

    assert quib.get_cache_behavior() == CacheBehavior.ON