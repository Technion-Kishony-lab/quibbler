import functools
import gc

import pytest
from matplotlib import widgets, pyplot as plt
from matplotlib.testing.decorators import image_comparison

from pyquibbler import iquib
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison


@pytest.fixture
def active_quib():
    return iquib(1)


@pytest.fixture
def radio_buttons(axes, active_quib):
    buttons = widgets.RadioButtons(
        ax=axes,
        labels=["a", "b", "c"],
        active=active_quib
    )
    plt.pause(0.01)
    return buttons


@quibbler_image_comparison(baseline_images=['set_active_multiple_times'])
def test_radio_buttons_set_active_multiple_times(get_only_live_widget, radio_buttons, active_quib, get_live_widgets):
    widget = get_only_live_widget()

    with count_redraws(radio_buttons) as redraw_count:
        widget.set_active(0)
        widget.set_active(1)
        widget.set_active(2)

    assert active_quib.get_value() == 2
    assert len(get_live_widgets()) == 1
    assert get_only_live_widget() is widget
    assert redraw_count.count == 3
