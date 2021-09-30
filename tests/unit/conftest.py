from unittest.mock import Mock, MagicMock

from pytest import fixture


class CopyableMock(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.args = args
        self.kwargs = kwargs

    def __copy__(self):
        return CopyableMock(*self.args, **self.kwargs)


@fixture
def function_mock_return_val():
    return CopyableMock(spec=['__setitem__'])


@fixture
def function_mock(function_mock_return_val):
    return Mock(return_value=function_mock_return_val)
