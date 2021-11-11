from unittest.mock import Mock, MagicMock

from pytest import fixture


@fixture
def function_mock_return_val():
    return [1, 2, 3, 4, 3, 2, 1]


@fixture
def function_mock(function_mock_return_val):
    func_mock = MagicMock(return_value=function_mock_return_val)
    func_mock.__name__ = 'func_mock'
    return func_mock
