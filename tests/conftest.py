from unittest.mock import Mock

from pytest import fixture

from pyquibbler.env import set_debug


@fixture(scope="session", autouse=True)
def use_debug_for_tests():
    set_debug(True)


@fixture
def function_mock_return_val():
    return object()


@fixture
def function_mock(function_mock_return_val):
    return Mock(return_value=function_mock_return_val)
