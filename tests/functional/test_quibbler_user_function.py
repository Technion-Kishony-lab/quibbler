from unittest import mock

import pytest

from pyquibbler import iquib, quiby, obj2quib
from pyquibbler.quib.quib import Quib


def test_quibbler_user_function_lazy():
    mock_func = mock.Mock()
    user_function = quiby(lazy=True)(mock_func)

    res = user_function()

    assert isinstance(res, Quib)
    assert mock_func.call_count == 0


def test_quibbler_user_function_non_lazy():
    mock_func = mock.Mock()
    user_function = quiby(lazy=False)(mock_func)

    res = user_function()

    assert isinstance(res, Quib)
    assert mock_func.call_count == 1


def test_quibbler_user_function_with_quibs():
    mock_func = mock.Mock()
    user_function = quiby(lazy=False, pass_quibs=True)(mock_func)
    quib = iquib(6)

    res = user_function(quib)

    assert isinstance(res, Quib)
    assert len(mock_func.mock_calls) == 1
    mock_call = mock_func.mock_calls[0]
    # It's not necessarily the quib itself- we just need to make sure it represents the quib
    arg_quib = mock_call.args[0]
    assert isinstance(arg_quib, Quib)
    assert arg_quib.get_value() == quib.get_value()


def test_quibbler_user_function_change_defintion_after_declearation():
    mock_func = mock.Mock()
    user_function = quiby(lazy=False)(mock_func)
    user_function.func_definition.lazy = True
    res = user_function()

    assert isinstance(res, Quib)
    assert mock_func.call_count == 0


def test_quibbler_user_function_uses_builtin_defintion():
    mock_func = mock.Mock()
    user_function = quiby(lazy=False)(mock_func)
    assert user_function.func_definition.lazy is False, "sanity"

    user_function = quiby(lazy=False)(str)
    assert user_function.func_definition.lazy is None


def test_quiby_creates_quiby_function():
    mock_func = mock.Mock()
    user_function = quiby(mock_func, lazy=True)

    res = user_function()

    assert isinstance(res, Quib)
    assert mock_func.call_count == 0


@pytest.mark.parametrize(['obj', 'expected_value'], [
    ([iquib(1)], [1]),
    ([iquib(1), 2, 3], [1, 2, 3]),
    ((iquib(1), 2, 3), (1, 2, 3)),
    ({'a': 1, 'b': iquib(2)}, {'a': 1, 'b': 2}),
    ((iquib(1), {'a': 10, 'b': iquib(20)}, 3), (1, {'a': 10, 'b': 20}, 3)),
])
def test_obj2quib(obj, expected_value):
    assert obj2quib(obj).get_value() == expected_value
