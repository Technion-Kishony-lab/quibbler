from unittest.mock import Mock

from pytest import fixture


@fixture
def function_mock_return_val():
    return object()


@fixture
def function_mock(function_mock_return_val):
    return Mock(return_value=function_mock_return_val)
