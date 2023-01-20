from unittest import mock

import pytest

from pyquibbler.function_definitions import FuncArgsKwargs
from pyquibbler.quib.graphics.event_handling import graphics_inverse_assigner, CanvasEventHandler
from pyquibbler.quib.graphics.event_handling.pick_handler import PickHandler


def test_canvas_event_handler_create_happy_flow():
    from pyquibbler.quib.graphics.event_handling.canvas_event_handler import CanvasEventHandler

    canvas = mock.Mock()

    handler = CanvasEventHandler.get_or_create_initialized_event_handler(canvas=canvas)
    handler_2 = CanvasEventHandler.get_or_create_initialized_event_handler(canvas=canvas)

    assert handler is handler_2
    canvas.mpl_connect.assert_called()


def test_canvas_event_handler_delete_itself_upon_figure_close():
    from pyquibbler.quib.graphics.event_handling.canvas_event_handler import CanvasEventHandler

    canvas = mock.Mock()
    canvas.events_to_funcs = {}
    canvas.figure = mock.Mock()
    canvas.figure.axes = []

    def mpl_connect(event, func):
        canvas.events_to_funcs[event] = func

    canvas.mpl_connect = mpl_connect
    handler = CanvasEventHandler.get_or_create_initialized_event_handler(canvas=canvas)

    number_of_handlers = len(CanvasEventHandler.CANVASES_TO_TRACKERS)

    canvas.events_to_funcs['close_event'](None)
    assert len(CanvasEventHandler.CANVASES_TO_TRACKERS) == number_of_handlers - 1


# NOTE: We're generally against calling private methods, but since the canvas is in charge of firing our handlers and
# we're mocking the canvas, we'll have to call our handlers ourselves

@pytest.fixture()
def canvas_event_handler():
    return CanvasEventHandler.get_or_create_initialized_event_handler(canvas=mock.Mock())


@pytest.fixture()
def mock_inverse_graphics_function(monkeypatch):
    mock_inverse = mock.Mock()
    monkeypatch.setattr(graphics_inverse_assigner, 'inverse_assign_drawing_func', mock_inverse)
    mock_inverse.return_value.overrides = [mock.Mock()]
    return mock_inverse


def test_canvas_event_handler_plot_drag_without_pick_event_does_nothing(canvas_event_handler,
                                                                        mock_inverse_graphics_function):
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_inverse_graphics_function.assert_not_called()


def test_canvas_event_handler_plot_drag(canvas_event_handler, mock_inverse_graphics_function):
    pick_event = mock.Mock()
    drawing_quib = mock.Mock()
    drawing_quib.handler = mock.Mock()
    drawing_quib.handler.func_args_kwargs = mock.Mock()
    pick_event.artist._quibbler_artist_creating_quib = drawing_quib
    canvas_event_handler._handle_pick_event(pick_event)
    mouse_event = mock.Mock()
    canvas_event_handler._handle_motion_notify(mouse_event)

    mock_inverse_graphics_function.assert_called_once_with(
        pick_handler=PickHandler(
            pick_event=pick_event,
            func_args_kwargs=drawing_quib.handler.func_args_kwargs),
        mouse_event=mouse_event,
        )


def test_canvas_event_handler_plot_drag_after_releasing(canvas_event_handler, mock_inverse_graphics_function):
    canvas_event_handler._handle_pick_event(mock.Mock())
    canvas_event_handler._handle_button_release(mock.Mock())
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_inverse_graphics_function.assert_not_called()


def test_canvas_event_handler_does_not_call_inverse_without_picking(canvas_event_handler,
                                                                    mock_inverse_graphics_function):
    canvas_event_handler._handle_motion_notify(mock.Mock())

    mock_inverse_graphics_function.assert_not_called()
