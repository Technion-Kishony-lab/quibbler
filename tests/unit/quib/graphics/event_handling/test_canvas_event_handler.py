from unittest import mock

import pytest

from pyquibbler.quib.graphics import CanvasEventHandler
from pyquibbler.quib.graphics.event_handling import graphics_reverse_assigner


def test_canvas_event_handler_create_happy_flow():
    canvas = mock.Mock()

    handler = CanvasEventHandler.get_or_create_initialized_event_handler(canvas=canvas)
    handler_2 = CanvasEventHandler.get_or_create_initialized_event_handler(canvas=canvas)

    assert handler is handler_2
    canvas.mpl_connect.assert_called()


# NOTE: We're generally against calling private methods, but since the canvas is in charge of firing our handlers and
# we're mocking the canvas, we'll have to call our handlers ourselves

@pytest.fixture()
def canvas_event_handler():
    return CanvasEventHandler.get_or_create_initialized_event_handler(canvas=mock.Mock())


@pytest.fixture()
def mock_reverse_graphics_function(monkeypatch):
    mock_reverse = mock.Mock()
    monkeypatch.setattr(graphics_reverse_assigner, 'reverse_graphics_function_quib', mock_reverse)
    return mock_reverse


def test_canvas_event_handler_plot_drag_without_pick_event_does_nothing(canvas_event_handler,
                                                                        mock_reverse_graphics_function):
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_reverse_graphics_function.assert_not_called()


def test_canvas_event_handler_plot_drag(canvas_event_handler, mock_reverse_graphics_function):
    pick_event = mock.Mock()
    graphics_function_quib = mock.Mock()
    pick_event.artist.graphics_function_quibs = [graphics_function_quib]
    canvas_event_handler._handle_pick_event(pick_event)
    mouse_event = mock.Mock()
    canvas_event_handler._handle_motion_notify(mouse_event)

    mock_reverse_graphics_function.assert_called_once_with(graphics_function_quib=graphics_function_quib,
                                                           mouse_event=mouse_event,
                                                           pick_event=pick_event)


def test_canvas_event_handler_plot_drag_after_releasing(canvas_event_handler, mock_reverse_graphics_function):
    canvas_event_handler._handle_pick_event(mock.Mock())
    canvas_event_handler._handle_button_release(mock.Mock())
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_reverse_graphics_function.assert_not_called()