import pytest
from matplotlib import pyplot as plt, widgets

from pyquibbler import iquib
from tests.integration.quib.graphics.widgets.utils import count_redraws, quibbler_image_comparison


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


@pytest.fixture
def list_of_bool_quibs():
    return [iquib(False), iquib(False), iquib(False)]


@pytest.fixture
def checkbox_list_of_quibs(axes, list_of_bool_quibs):
    checkbox = widgets.CheckButtons(
        ax=axes,
        labels=['Red', 'Green', 'Blue'],
        actives=list_of_bool_quibs
    )
    plt.pause(0.01)
    return checkbox


@pytest.mark.regression
@quibbler_image_comparison(baseline_images=['multiple_sets'])
def test_checkbox_multiple_sets(axes, get_only_live_widget, get_live_artists, get_live_widgets,
                                checkbox_quib, actives_quib):
    widget = get_only_live_widget()
    original_num_artists = len(get_live_artists())
    with count_redraws(checkbox_quib) as redraw_count:
        widget.set_active(0)
        widget.set_active(1)
        widget.set_active(2)

    assert len(axes.patches) == 3
    assert len(axes.texts) == 3
    assert len(axes.lines) == 6
    assert len(get_live_artists()) == original_num_artists
    assert len(get_live_widgets()) == 1

    assert actives_quib.get_value() == [True, True, True]
    assert redraw_count.count == 3


@quibbler_image_comparison(baseline_images=['unset'])
def test_checkbox_unset(get_only_live_widget, checkbox_quib, actives_quib):
    widget = get_only_live_widget()

    with count_redraws(checkbox_quib) as redraw_count:
        widget.set_active(0)
        widget.set_active(0)

    assert actives_quib.get_value() == [False, False, False]
    assert redraw_count.count == 2


def test_set_quib_in_checkbox_of_list_of_quibs(get_only_live_widget, checkbox_list_of_quibs, list_of_bool_quibs):
    widget = get_only_live_widget()

    with count_redraws(checkbox_list_of_quibs) as redraw_count:
        widget.set_active(1)

    assert [quib.get_value() for quib in list_of_bool_quibs] == [False, True, False]
    assert redraw_count.count == 1


def test_unset_quib_in_checkbox_of_list_of_quibs(get_only_live_widget, checkbox_list_of_quibs, list_of_bool_quibs):
    widget = get_only_live_widget()

    with count_redraws(checkbox_list_of_quibs) as redraw_count:
        widget.set_active(1)
        widget.set_active(1)

    assert [quib.get_value() for quib in list_of_bool_quibs] == [False, False, False]
    assert redraw_count.count == 2

