import pytest
from matplotlib import widgets, pyplot as plt

from pyquibbler import iquib


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


def test_radio_buttons_set_active_multiple_times(get_only_live_widget, radio_buttons, active_quib, get_live_widgets):
    widget = get_only_live_widget()
    get_only_live_widget().set_active(0)
    get_only_live_widget().set_active(1)
    get_only_live_widget().set_active(2)
    get_only_live_widget().set_active(1)

    assert active_quib.get_value() == 1
    assert len(get_live_widgets()) == 1
    assert get_only_live_widget() is widget


