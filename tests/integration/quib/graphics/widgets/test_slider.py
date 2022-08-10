import matplotlib.pyplot as plt
import pytest
from matplotlib import widgets

from pyquibbler import iquib, undo
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison, count_canvas_draws


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

    initial_live_widgets = len(get_live_widgets())

    create_button_press_event(*get_axes_start())
    create_button_release_event(*get_axes_start())

    assert input_quib.get_value() == 0
    assert len(get_live_widgets()) == initial_live_widgets


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
def test_slider_graphics_function_quib_calls_multiple_times(axes, get_live_widgets, get_live_artists, input_quib,
                                                            create_button_press_event,
                                                            create_motion_notify_event,
                                                            create_button_release_event, get_axes_start,
                                                            slider_quib, get_axes_end, get_axes_middle):
    original_num_artists = len(get_live_artists())

    with count_redraws(slider_quib) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_button_press_event(*get_axes_start())
        create_motion_notify_event(*get_axes_end())
        create_button_release_event(*get_axes_end())

        create_button_press_event(*get_axes_start())
        create_motion_notify_event(*get_axes_end())
        create_button_release_event(*get_axes_end())

    assert canvas_redraw_count.count == 4
    assert redraw_count.count == 4  # 2 x press + 2 x motion
    assert len(get_live_widgets()) == 1
    assert len(get_live_artists()) == original_num_artists


def test_slider_undo_redo(axes, get_live_widgets, get_live_artists, input_quib,
                          create_button_press_event,
                          create_motion_notify_event,
                          create_button_release_event, get_axes_start,
                          slider_quib, get_axes_end, get_axes_middle):

        assert input_quib.get_value() == 2

        create_button_press_event(*get_axes_middle())
        assert input_quib.get_value() == 1

        create_motion_notify_event(*get_axes_start())
        assert input_quib.get_value() == 0
        create_button_release_event(*get_axes_start())
        assert input_quib.get_value() == 0

        undo()
        assert input_quib.get_value() == 2


def test_slider_rightclick_sets_to_default(axes, get_live_widgets, get_live_artists, input_quib,
                                           create_button_press_event,
                                           create_motion_notify_event,
                                           create_button_release_event, get_axes_start,
                                           slider_quib, get_axes_end, get_axes_middle):

        assert input_quib.get_value() == 2

        create_button_press_event(*get_axes_middle())
        create_button_release_event(*get_axes_middle())
        assert input_quib.get_value() == 1

        create_button_press_event(*get_axes_middle(), button=3)  # right-click
        create_button_release_event(*get_axes_middle(), button=3)

        assert input_quib.get_value() == 2

        undo()
        assert input_quib.get_value() == 1

        undo()
        assert input_quib.get_value() == 2
