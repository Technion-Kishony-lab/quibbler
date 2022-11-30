import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import widgets

from pyquibbler import iquib, undo, default
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison, count_canvas_draws


@pytest.fixture()
def input_quib1():
    return iquib(1)


@pytest.fixture()
def input_quib2():
    return iquib(2)


@pytest.fixture()
def input_quib_list():
    return iquib([1, 2])


@pytest.fixture
def range_slider_quib(axes, input_quib1, input_quib2):
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


@pytest.fixture
def range_slider_quib_of_list_quib(axes, input_quib_list):
    slider = widgets.RangeSlider(
        ax=axes,
        valinit=input_quib_list,
        label="Pasten",
        valmax=4,
        valmin=0,
        valstep=1
    )
    plt.pause(0.01)
    return slider


def test_range_slider_graphics_function_quib_press_and_release_changes(
        axes, get_live_widgets, range_slider_quib, input_quib1, input_quib2, create_axes_mouse_press_move_release_events):

    initial_live_widgets = len(get_live_widgets())
    assert input_quib1.get_value() == 1, "sanity"
    create_axes_mouse_press_move_release_events(['left'])

    assert input_quib1.get_value() == 0
    assert len(get_live_widgets()) == initial_live_widgets


def test_range_slider_graphics_function_quib_press_and_release_changes_with_list_quib(
        axes, range_slider_quib_of_list_quib, input_quib_list, create_axes_mouse_press_move_release_events):

    create_axes_mouse_press_move_release_events(['left'])

    print(input_quib_list.get_value())
    assert input_quib_list.get_value() == [0, 2]


def test_range_slider_graphics_function_quib_press_and_motion_notify_changes_and_keeps_same_widget(
        axes, create_axes_mouse_press_move_release_events, get_live_widgets, range_slider_quib, input_quib1, input_quib2):

    initial_live_widgets = len(get_live_widgets())
    widget = range_slider_quib.get_value()

    create_axes_mouse_press_move_release_events(['middle', 'right'])
    assert [input_quib1.get_value(), input_quib2.get_value()] == [1, 4]

    assert range_slider_quib.get_value() is widget
    assert len(get_live_widgets()) == initial_live_widgets


def test_range_slider_rightclick_sets_to_default(axes, get_live_widgets, get_live_artists, input_quib1, input_quib2, range_slider_quib,
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


@pytest.mark.regression
def test_range_slider_value_after_reset_to_default(
        axes, range_slider_quib_of_list_quib, input_quib_list, create_axes_mouse_press_move_release_events):

    slider = range_slider_quib_of_list_quib.get_value()
    assert np.array_equal(slider.val, [1, 2]), "sanity"
    create_axes_mouse_press_move_release_events(['left'])
    assert input_quib_list.get_value() == [0, 2], "sanity"
    assert np.array_equal(slider.val, [0, 2]), "sanity"

    input_quib_list.assign(default)
    # create_axes_mouse_press_move_release_events(['middle'], button=3)  # right-click
    assert input_quib_list.get_value() == [1, 2], "sanity"

    assert slider is range_slider_quib_of_list_quib.get_value()
    # this was the bug:
    assert np.array_equal(slider.val, [1, 2])


@pytest.mark.regression
def test_range_slider_value_changes_when_quib_change(
        axes, range_slider_quib_of_list_quib, input_quib_list, create_axes_mouse_press_move_release_events):

    slider = range_slider_quib_of_list_quib.get_value()
    assert np.array_equal(slider.val, [1, 2]), "sanity"
    input_quib_list.assign(0, 0)
    assert np.array_equal(slider.val, [0, 2])
