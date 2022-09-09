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


def test_slider_press_and_motion_notify_changes(axes, slider, callback, create_axes_mouse_press_move_release_events):

    assert isinstance(slider, QSlider)
    assert slider.val == 2

    create_axes_mouse_press_move_release_events(['right', 'middle'])

    assert slider.val == 1
    callback.assert_called_once()
