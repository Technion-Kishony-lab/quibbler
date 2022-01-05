import time
from unittest import mock

import pytest

from pyquibbler.refactor.performance_utils import timer, get_timer, Timer, TimerNotFoundException


@pytest.fixture
def mock_time():
    original_time = time.time
    time.time = mock.Mock()
    yield time.time
    time.time = original_time


def test_timer_happy_flow(mock_time):
    name = "myfavtimezzz"
    mock_time.side_effect = [0, 1]

    with timer(name=name):
        pass

    created_timer = get_timer(name)
    assert created_timer.total_time == 1
    assert created_timer.total_count == 1


def test_timer_called_twice(mock_time):
    name = "calltwiceee"
    mock_time.side_effect = [0, 1, 0, 1]

    with timer(name=name):
        pass
    with timer(name=name):
        pass

    created_timer = get_timer(name)
    assert created_timer.total_time == 2
    assert created_timer.total_count == 2


def test_timer_calls_callback(mock_time):
    name = "callac"
    mock_time.side_effect = [0, 1]
    mock_callback = mock.Mock()

    with timer(name=name, callback=mock_callback):
        pass

    mock_callback.assert_called_once_with(1)


def test_timer_raises_exception_for_unknown_timer(mock_time):
    with pytest.raises(TimerNotFoundException):
        get_timer('unknown')


def test_timer_repr():
    fake_timer = Timer(name="pasten", total_time=1, total_count=1)

    # Make sure this doesn't fail
    repr(fake_timer)

