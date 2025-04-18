from unittest import mock

import matplotlib.pyplot as plt
import numpy as np
import pytest
from matplotlib import widgets

from .....conftest import plt_pause
from pyquibbler.graphics.widgets import QSlider, QRangeSlider


@pytest.fixture
def callback1():
    return mock.Mock()


@pytest.fixture
def callback2():
    return mock.Mock()


@pytest.fixture
def slider(axes, callback1):
    slider = widgets.Slider(
        ax=axes,
        valinit=2,
        label="Pasten",
        valmax=2,
        valmin=0,
        valstep=1
    )
    plt_pause(0.01)
    slider.on_changed(callback1)
    return slider


@pytest.fixture
def range_slider(axes, callback2):
    slider = widgets.RangeSlider(
        ax=axes,
        valinit=[0.0, 2.0],
        label="Pasten",
        valmax=2.,
        valmin=0.,
        valstep=1
    )
    plt_pause(0.01)
    slider.on_changed(callback2)
    return slider


def test_slider_press_and_motion_notify_changes(axes, slider, callback1, create_axes_mouse_press_move_release_events):

    assert isinstance(slider, QSlider)
    assert slider.val == 2

    create_axes_mouse_press_move_release_events(['right', 'middle'])

    assert slider.val == 1
    callback1.assert_called_once()


def test_range_slider_press_and_motion_notify_changes(axes, range_slider, callback2, create_axes_mouse_press_move_release_events):

    assert isinstance(range_slider, QRangeSlider)
    assert np.array_equal(range_slider.val, [0, 2])

    create_axes_mouse_press_move_release_events(['right', 'middle'])

    assert np.array_equal(range_slider.val, [1, 2])
