import pytest
from unittest import mock
from pyquibbler import iquib, CacheStatus, Quib
from pyquibbler.quib.graphics import aggregate_redraw_mode


@pytest.fixture
def func():
    return mock.Mock()


@pytest.fixture
def quib() -> Quib:
    return iquib(1)


def test_add_and_remove_callback_func(quib, func):
    quib.add_callback(func)
    assert quib.get_callbacks() == {func}

    quib.remove_callback(func)
    assert quib.get_callbacks() == set()


def test_callback_quib_is_graphics(quib, func):
    assert quib.is_graphics_quib is False, "sanity"
    quib.add_callback(func)
    assert quib.is_graphics_quib is True


def test_quib_is_evaluated_when_first_callback_is_added(func, quib):
    b = quib + 10

    assert b.cache_status is CacheStatus.ALL_INVALID, "sanity"

    b.add_callback(func)
    assert b.cache_status is CacheStatus.ALL_VALID


def test_callback_func_of_iquib_is_called_with_new_value(func, quib):
    quib.add_callback(func)
    func.assert_not_called(), "sanity"

    quib.assign(2)
    func.assert_called_once()
    assert func.mock_calls[0].args == (2, )


def test_callback_func_of_fquib_is_called_with_new_value(func, quib):
    b = quib + 10

    b.add_callback(func)
    func.assert_not_called()

    quib.assign(2)
    func.assert_called_once()
    assert func.mock_calls[0].args == (12, )


def test_callback_func_is_only_called_once_in_aggregate_redraw(func, quib):
    b = quib + 10

    b.add_callback(func)

    with aggregate_redraw_mode():
        quib.assign(101)
        quib.assign(102)

    func.assert_called_once()

