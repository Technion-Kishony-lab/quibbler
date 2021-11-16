import matplotlib.pyplot as plt
import objgraph
import pytest
from matplotlib import widgets

from pyquibbler import iquib


@pytest.fixture()
def input_quib():
    return iquib(2)


@pytest.fixture
def slider_quib(axes, input_quib):
    slider = widgets.Slider(
        ax=axes,
        valinit=input_quib,
        label="Pasten",
        valmax=2,
        valmin=0,
        valstep=1
    )
    plt.pause(0.01)
    return slider


def test_slider_graphics_function_quib_press_and_release_changes(axes, get_live_widgets, slider_quib, input_quib,
                                                                 create_button_press_event,
                                                                 create_button_release_event, get_axes_start):
    create_button_press_event(*get_axes_start())
    create_button_release_event(*get_axes_start())

    assert input_quib.get_value() == 0
    assert len(get_live_widgets()) == 1


def test_slider_graphics_function_quib_press_and_motion_notify_changes_and_keeps_same_widget(axes,
                                                                                             get_live_widgets,
                                                                                             create_button_press_event,
                                                                                             get_axes_end,
                                                                                             get_axes_middle,
                                                                                             create_motion_notify_event,
                                                                                             slider_quib, input_quib,
                                                                                             ):
    widget = slider_quib.get_value()
    create_button_press_event(*get_axes_end())
    create_motion_notify_event(*get_axes_middle())

    assert input_quib.get_value() == 1
    assert slider_quib.get_value() is widget
    assert len(get_live_widgets()) == 1


@pytest.mark.regression
def test_slider_graphics_function_quib_calls_on_change_once(axes, get_live_widgets, input_quib,
                                                            create_button_press_event,
                                                            create_motion_notify_event,
                                                            create_button_release_event, get_axes_start,
                                                            slider_quib, get_axes_end):
    previous_redraw = slider_quib.redraw_if_appropriate
    redraw_count = 0

    def redraw(*args, **kwargs):
        nonlocal redraw_count
        redraw_count += 1
        return previous_redraw(*args, **kwargs)

    slider_quib.redraw_if_appropriate = redraw

    create_button_press_event(*get_axes_start())
    create_motion_notify_event(*get_axes_end())
    create_button_release_event(*get_axes_end())

    create_button_press_event(*get_axes_start())
    create_motion_notify_event(*get_axes_end())
    create_button_release_event(*get_axes_end())

    assert redraw_count == 6  # press * 2 + motion * 2 + release * 2
    # import ipdb; ipdb.set_trace()
    assert len(get_live_widgets()) == 1
