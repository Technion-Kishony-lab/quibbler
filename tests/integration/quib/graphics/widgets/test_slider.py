import matplotlib.pyplot as plt
import pytest
from matplotlib import widgets

from pyquibbler import iquib
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison


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


@quibbler_image_comparison(baseline_images=['press_and_release_changes'])
def test_slider_graphics_function_quib_press_and_release_changes(axes, get_live_widgets, slider_quib, input_quib,
                                                                 create_button_press_event,
                                                                 create_button_release_event, get_axes_start):
    create_button_press_event(*get_axes_start())
    create_button_release_event(*get_axes_start())

    assert input_quib.get_value() == 0
    assert len(get_live_widgets()) == 1


@quibbler_image_comparison(baseline_images=['keeps_same_widget'])
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
@quibbler_image_comparison(baseline_images=['multiple_times'])
def test_slider_graphics_function_quib_calls_multiple_times(axes, get_live_widgets, input_quib,
                                                            create_button_press_event,
                                                            create_motion_notify_event,
                                                            create_button_release_event, get_axes_start,
                                                            slider_quib, get_axes_end, get_axes_middle):
    with count_redraws(slider_quib) as redraw_count:
        create_button_press_event(*get_axes_start())
        create_motion_notify_event(*get_axes_end())
        create_button_release_event(*get_axes_end())

        create_button_press_event(*get_axes_start())
        create_motion_notify_event(*get_axes_end())
        create_button_release_event(*get_axes_end())

    assert redraw_count.count == 4  # press * 2 + motion * 2
    assert len(get_live_widgets()) == 1
