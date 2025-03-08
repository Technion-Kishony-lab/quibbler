import matplotlib.pyplot as plt
import pytest
from matplotlib import widgets

from .....conftest import get_axes, create_mouse_press_move_release_events
from pyquibbler import iquib, undo
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison, count_canvas_draws


@pytest.fixture()
def input_quib():
    return iquib(2)


def create_slider(axes, valinit):
    slider = widgets.Slider(
        ax=axes,
        valinit=valinit,
        label="Pasten",
        valmax=2,
        valmin=0,
        valstep=1
    )
    plt.pause(0.01)
    return slider


@quibbler_image_comparison(baseline_images=['press_and_release_changes'])
def test_slider_graphics_function_quib_press_and_release_changes(live_widgets, input_quib):

    axes = get_axes()
    slider = create_slider(axes, input_quib)
    initial_live_widgets = len(live_widgets)
    create_mouse_press_move_release_events(axes, ['left'])
    assert input_quib.get_value() == 0
    assert len(live_widgets) == initial_live_widgets


@quibbler_image_comparison(baseline_images=['keeps_same_widget'])
def test_slider_graphics_function_quib_press_and_motion_notify_changes_and_keeps_same_widget(live_widgets, input_quib):

    axes = get_axes()
    slider_quib = create_slider(axes, input_quib)
    widget = slider_quib.get_value()
    create_mouse_press_move_release_events(axes, ['left', 'middle'])

    assert input_quib.get_value() == 1
    assert slider_quib.get_value() is widget
    assert len(live_widgets) == 1


@pytest.mark.regression
@quibbler_image_comparison(baseline_images=['multiple_times'])
def test_slider_graphics_function_quib_calls_multiple_times(live_widgets, live_artists, input_quib):
    axes = get_axes()
    slider_quib = create_slider(axes, input_quib)
    for a in axes.get_children():
        a.get_children()  # makes the axes create all its x/y-tick artists

    original_num_artists = len(live_artists)

    with count_redraws(slider_quib) as redraw_count, \
            count_canvas_draws(axes.figure.canvas) as canvas_redraw_count:
        create_mouse_press_move_release_events(axes, ['left', 'right'])
        create_mouse_press_move_release_events(axes, ['left', 'right'])

    assert canvas_redraw_count.count == 4
    assert redraw_count.count == 4  # 2 x press + 2 x motion
    assert len(live_widgets) == 1
    assert len(live_artists) == original_num_artists


def test_slider_undo_redo(axes, live_widgets, live_artists, input_quib):
    slider_quib = create_slider(axes, input_quib)
    assert input_quib.get_value() == 2

    create_mouse_press_move_release_events(axes, ['middle'], release=False)
    assert input_quib.get_value() == 1

    create_mouse_press_move_release_events(axes, ['middle', 'left'], press=False, release=False)
    assert input_quib.get_value() == 0
    create_mouse_press_move_release_events(axes, ['left'], press=False)
    assert input_quib.get_value() == 0

    undo()
    assert input_quib.get_value() == 2


def test_slider_rightclick_sets_to_default(axes, live_widgets, live_artists, input_quib):
    slider_quib = create_slider(axes, input_quib)
    assert input_quib.get_value() == 2

    create_mouse_press_move_release_events(axes, ['middle'])
    assert input_quib.get_value() == 1

    create_mouse_press_move_release_events(axes, ['middle'], button=3)  # right-click

    assert input_quib.get_value() == 2

    undo()
    assert input_quib.get_value() == 1

    undo()
    assert input_quib.get_value() == 2
