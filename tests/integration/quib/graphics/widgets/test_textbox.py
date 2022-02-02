import pytest
from matplotlib import widgets, pyplot as plt

from pyquibbler import iquib


@pytest.fixture()
def input_quib():
    return iquib("")


@pytest.fixture
def textbox_quib(axes, input_quib):
    slider = widgets.TextBox(
        ax=axes,
        label="hello",
        initial=input_quib
    )
    plt.pause(0.01)
    return slider


def test_textbox(input_quib, textbox_quib, create_button_press_event, create_button_release_event, get_axes_start, get_axes_middle,
                 get_axes_end, create_key_press_and_release_event):
    create_button_press_event(*get_axes_start())
    create_button_release_event(*get_axes_start())
    create_key_press_and_release_event('h')
    create_key_press_and_release_event('enter')

    assert input_quib.get_value() == 'h'