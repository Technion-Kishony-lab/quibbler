import pytest
from matplotlib import pyplot as plt, widgets

from pyquibbler import iquib
from tests.integration.quib.graphics.widgets.utils import count_redraws


@pytest.fixture
def actives_quib():
    return iquib([False, False, False])


@pytest.fixture
def checkbox_quib(axes, actives_quib):
    checkbox = widgets.CheckButtons(
        ax=axes,
        labels=['Red', 'Green', 'Blue'],
        actives=actives_quib
    )
    plt.pause(0.01)
    return checkbox


@pytest.mark.regression
def test_checkbox_multiple_sets(get_only_live_widget, checkbox_quib, actives_quib):
    widget = get_only_live_widget()

    with count_redraws(checkbox_quib) as redraw_count:
        widget.set_active(0)
        widget.set_active(1)
        widget.set_active(2)

    assert actives_quib.get_value() == [True, True, True]
    assert redraw_count.count == 3
