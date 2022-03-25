from unittest import mock

from pyquibbler import quibbler_user_function, iquib
from pyquibbler.quib import Quib


def test_quibbler_user_function_lazy():
    mock_func = mock.Mock()
    user_function = quibbler_user_function(lazy=True)(mock_func)

    res = user_function()

    assert isinstance(res, Quib)
    assert mock_func.call_count == 0


def test_quibbler_user_function_non_lazy():
    mock_func = mock.Mock()
    user_function = quibbler_user_function(lazy=False)(mock_func)

    res = user_function()

    assert isinstance(res, Quib)
    assert mock_func.call_count == 1


def test_quibbler_user_function_with_quibs():
    mock_func = mock.Mock()
    user_function = quibbler_user_function(pass_quibs=True, lazy=False)(mock_func)
    quib = iquib(6)

    res = user_function(quib)

    assert isinstance(res, Quib)
    assert len(mock_func.mock_calls) == 1
    mock_call = mock_func.mock_calls[0]
    # It's not necessarily the quib itself- we just need to make sure it represents the quib
    arg_quib = mock_call.args[0]
    assert isinstance(arg_quib, Quib)
    assert arg_quib.get_value() == quib.get_value()

