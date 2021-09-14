from unittest.mock import Mock

from pytest import fixture

from pyquibbler import CacheBehavior
from pyquibbler.env import set_debug
from pyquibbler.quib import FunctionQuib


@fixture(scope="session", autouse=True)
def setup_environment_for_tests():
    set_debug(True)
    FunctionQuib.DEFAULT_CACHE_BEHAVIOR = CacheBehavior.ON


@fixture
def function_mock_return_val():
    return object()


@fixture
def function_mock(function_mock_return_val):
    return Mock(return_value=function_mock_return_val)
