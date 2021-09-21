from unittest import mock

from pyquibbler import quibbler_user_function
from pyquibbler.quib import HolisticFunctionQuib


def test_quibbler_user_function_lazy():
    mock_func = mock.Mock()
    user_function = quibbler_user_function(lazy=True)(mock_func)

    res = user_function()

    assert isinstance(res, HolisticFunctionQuib)
    assert mock_func.call_count == 0


def test_quibbler_user_function_non_lazy():
    mock_func = mock.Mock()
    user_function = quibbler_user_function(lazy=False)(mock_func)

    res = user_function()

    assert isinstance(res, HolisticFunctionQuib)
    assert mock_func.call_count == 1

