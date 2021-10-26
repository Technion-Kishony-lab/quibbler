from unittest import mock

import pytest

from pyquibbler.quib.graphics import CanvasEventHandler
from pyquibbler.quib.graphics.event_handling import graphics_inverse_assigner


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
def mock_inverse_graphics_function(monkeypatch):
    mock_inverse = mock.Mock()
    monkeypatch.setattr(graphics_inverse_assigner, 'inverse_assign_drawing_func', mock_inverse)
    return mock_inverse


def test_canvas_event_handler_plot_drag_without_pick_event_does_nothing(canvas_event_handler,
                                                                        mock_inverse_graphics_function):
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_inverse_graphics_function.assert_not_called()


def test_canvas_event_handler_plot_drag(canvas_event_handler, mock_inverse_graphics_function):
    pick_event = mock.Mock()
    drawing_func = mock.Mock()
    pick_event.artist._quibbler_drawing_func = drawing_func
    pick_event.artist._quibbler_args = [mock.Mock()]
    canvas_event_handler._handle_pick_event(pick_event)
    mouse_event = mock.Mock()
    canvas_event_handler._handle_motion_notify(mouse_event)

    mock_inverse_graphics_function.assert_called_once_with(drawing_func=drawing_func,
                                                           args=pick_event.artist._quibbler_args,
                                                           mouse_event=mouse_event,
                                                           pick_event=pick_event)


def test_canvas_event_handler_plot_drag_after_releasing(canvas_event_handler, mock_inverse_graphics_function):
    canvas_event_handler._handle_pick_event(mock.Mock())
    canvas_event_handler._handle_button_release(mock.Mock())
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_inverse_graphics_function.assert_not_called()


def test_canvas_event_handler_raises_exception(canvas_event_handler,
                                                                        mock_inverse_graphics_function):
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_inverse_graphics_function.assert_not_called()