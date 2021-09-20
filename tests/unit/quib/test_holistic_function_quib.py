from unittest import mock

import pytest

from pyquibbler.graphics import overriding
from pyquibbler.graphics.overriding import GraphicsFunctionCall
from pyquibbler.quib.holistic_function_quib import HolisticFunctionQuib


def create_mock_artist():
    artist = mock.Mock()
    artist.axes.artists = [artist]
    return artist


@pytest.fixture()
def mock_artists_collected(monkeypatch):
    artists = [create_mock_artist()]
    monkeypatch.setattr(overriding, "get_artists_collected", lambda *_, **__: artists)
    return artists


@pytest.fixture()
def mock_graphics_calls_collected(monkeypatch):
    graphics_call = mock.Mock()
    graphics_call.return_value = [create_mock_artist()]
    monkeypatch.setattr(overriding, "get_graphics_calls_collected", lambda *_, **__: [GraphicsFunctionCall(
        func=graphics_call,
        args=tuple(),
        kwargs={}
    )])
    return [graphics_call]


def test_holistic_function_quib_get_value_returns_value():
    mock_func = mock.Mock()
    quib = HolisticFunctionQuib(
        args=tuple(),
        kwargs={},
        artists_redrawers=set(),
        cache_behavior=None,
        children=[],
        func=mock_func,
        graphics_calls=[]
    )

    res = quib.get_value()

    assert res == mock_func.return_value


def test_holistic_function_quib_removes_artists_created(mock_artists_collected):
    quib = HolisticFunctionQuib(
        args=tuple(),
        kwargs={},
        artists_redrawers=set(),
        cache_behavior=None,
        children=[],
        func=mock.Mock(),
        graphics_calls=[]
    )

    quib.get_value()

    for artist in mock_artists_collected:
        artist.remove.assert_called_once()


def test_holistic_function_quib_run_and_redraw_calls_func_and_graphics(mock_graphics_calls_collected):
    mock_holistic_func = mock.Mock()
    quib = HolisticFunctionQuib.create(
        func_args=tuple(),
        func_kwargs={},
        func=mock_holistic_func
    )

    quib.run_if_needed_and_draw()

    for graphics_call in mock_graphics_calls_collected:
        graphics_call.assert_called_once()
    mock_holistic_func.assert_called_once()


def test_holistic_function_quib_repeated_calls(mock_graphics_calls_collected):
    mock_holistic_func = mock.Mock()
    quib = HolisticFunctionQuib.create(
        func_args=tuple(),
        func_kwargs={},
        func=mock_holistic_func
    )

    quib.get_value()
    quib.get_value()
    quib.run_if_needed_and_draw()
    quib.run_if_needed_and_draw()

    for mock_graphics_call in mock_graphics_calls_collected:
        assert mock_graphics_call.call_count == 2
    mock_holistic_func.assert_called_once()
