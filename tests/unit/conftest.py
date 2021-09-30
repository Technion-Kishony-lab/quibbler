from unittest.mock import Mock

from pytest import fixture


@fixture
def function_mock_return_val():
    return [1, 2, 3, 4, 3, 2, 1]


@fixture
def function_mock(function_mock_return_val):
    return Mock(return_value=function_mock_return_val)
