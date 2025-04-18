import pytest
from matplotlib import widgets, pyplot as plt

from .....conftest import create_mouse_press_move_release_events, plt_pause
from pyquibbler import iquib


@pytest.fixture()
def input_quib():
    return iquib("")


def create_textbox_quib(ax, initial):
    widget = widgets.TextBox(
        ax=ax,
        label="hello",
        initial=initial
    )
    plt_pause(0.01)
    return widget


def test_textbox(axes, input_quib, live_artists):
    textbox_quib = create_textbox_quib(axes, input_quib)
    original_num_artists = len(live_artists)

    textbox = textbox_quib.get_value()
    assert textbox.text_disp is axes.texts[1], "sanity"

    create_mouse_press_move_release_events(axes, ['middle'])
    # create_key_press_and_release_event(axes, 'h')
    # create_key_press_and_release_event(axes, 'enter')
    textbox.set_val('h')
    assert textbox.text_disp is axes.texts[1]

    assert input_quib.get_value() == 'h'
    assert len(live_artists) == original_num_artists


def test_text_box_with_numeric_value(axes):
    x = iquib(7)
    text_box_quib = widgets.TextBox(
            ax=axes,
            label="number",
            initial=x
        )
    text_box = text_box_quib.get_value()
    plt_pause(0.01)
    create_mouse_press_move_release_events(axes, ['middle'])
    # create_key_press_and_release_event('9')
    # create_key_press_and_release_event('enter')
    text_box.set_val('79')


    assert x.get_value() == 79
