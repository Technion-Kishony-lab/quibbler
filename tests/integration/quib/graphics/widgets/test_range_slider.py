import matplotlib.pyplot as plt
import pytest
from matplotlib import widgets

from pyquibbler import iquib, undo
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison, count_canvas_draws


@pytest.fixture()
def input_quib1():
    return iquib(1)


@pytest.fixture()
def input_quib2():
    return iquib(2)


@pytest.fixture
def slider_quib(axes, input_quib1, input_quib2):
    slider = widgets.RangeSlider(
        ax=axes,
        valinit=[input_quib1, input_quib2],
        label="Pasten",
        valmax=4,
        valmin=0,
        valstep=1
    )
    plt.pause(0.01)
    return slider


def test_range_slider_graphics_function_quib_press_and_release_changes(axes, get_live_widgets, slider_quib, input_quib1, input_quib2,
                                                                 create_axes_mouse_press_move_release_events):

    initial_live_widgets = len(get_live_widgets())
    assert input_quib1.get_value() == 1, "sanity"
    create_axes_mouse_press_move_release_events(['left'])

    assert input_quib1.get_value() == 0
    assert len(get_live_widgets()) == initial_live_widgets


def test_range_slider_graphics_function_quib_press_and_motion_notify_changes_and_keeps_same_widget(
        axes, create_axes_mouse_press_move_release_events, get_live_widgets, slider_quib, input_quib1, input_quib2):

    widget = slider_quib.get_value()

    create_axes_mouse_press_move_release_events(['middle', 'right'])
    assert [input_quib1.get_value(), input_quib2.get_value()] == [1, 4]

    assert slider_quib.get_value() is widget
    assert len(get_live_widgets()) == 1


def test_range_slider_rightclick_sets_to_default(axes, get_live_widgets, get_live_artists, input_quib1, input_quib2, slider_quib,
                                                 create_axes_mouse_press_move_release_events):

    assert input_quib2.get_value() == 2

    create_axes_mouse_press_move_release_events(['right'])
    assert input_quib2.get_value() == 4

    create_axes_mouse_press_move_release_events(['middle'], button=3)  # right-click

    assert input_quib2.get_value() == 2

    undo()
    assert input_quib2.get_value() == 4

    undo()
    assert input_quib2.get_value() == 2
