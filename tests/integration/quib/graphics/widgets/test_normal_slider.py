from unittest import mock

import matplotlib.pyplot as plt
import pytest
from matplotlib import widgets

from pyquibbler.graphics.widgets import QSlider


@pytest.fixture
def callback():
    return mock.Mock()


@pytest.fixture
def slider(axes, callback):
    slider = widgets.Slider(
        ax=axes,
        valinit=2,
        label="Pasten",
        valmax=2,
        valmin=0,
        valstep=1
    )
    plt.pause(0.01)
    slider.on_changed(callback)
    return slider


def test_slider_press_and_motion_notify_changes(axes,
                                                create_button_press_event,
                                                create_button_release_event,
                                                get_axes_end,
                                                get_axes_middle,
                                                create_motion_notify_event,
                                                slider, callback
                                                ):

    assert isinstance(slider, QSlider)
    assert slider.val == 2

    create_button_press_event(*get_axes_end())
    create_motion_notify_event(*get_axes_middle())
    create_button_release_event(*get_axes_middle())

    assert slider.val == 1
    callback.assert_called_once()
