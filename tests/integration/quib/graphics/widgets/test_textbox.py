import pytest
from matplotlib import widgets, pyplot as plt

from pyquibbler import iquib


@pytest.fixture()
def input_quib():
    return iquib("")


@pytest.fixture
def textbox_quib(axes, input_quib):
    widget = widgets.TextBox(
        ax=axes,
        label="hello",
        initial=input_quib
    )
    plt.pause(0.01)
    return widget


def test_textbox(input_quib, textbox_quib, get_live_artists, axes,
                 create_axes_mouse_press_move_release_events, create_key_press_and_release_event):

    original_num_artists = len(get_live_artists())

    textbox = textbox_quib.get_value()
    assert textbox.text_disp is axes.texts[1], "sanity"

    create_axes_mouse_press_move_release_events(['middle'])
    create_key_press_and_release_event('h')
    create_key_press_and_release_event('enter')
    assert textbox.text_disp is axes.texts[1]

    assert input_quib.get_value() == 'h'
    assert len(get_live_artists()) == original_num_artists
