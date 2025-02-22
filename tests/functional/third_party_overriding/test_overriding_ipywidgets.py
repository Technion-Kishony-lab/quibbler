import pytest
import ipywidgets

from unittest import mock

from pyquibbler import iquib, Project
from pyquibbler.function_overriding.third_party_overriding.ipywidgets.overrides import \
    _get_or_create_trait_to_quiby_widget_trait
from pyquibbler.function_overriding.third_party_overriding.ipywidgets.quiby_widget_trait import UNDO_GROUP_TIME
from tests.integration.quib.graphics.widgets.utils import count_invalidations

def simulate_time_delay(w, attr='value'):
    quiby_widget_trait = _get_or_create_trait_to_quiby_widget_trait(w)[attr]
    quiby_widget_trait.denounce_timer.call_now()


@pytest.fixture
def widget(quib):
    yield ipywidgets.FloatSlider(value=quib, min=0, max=10, step=1)


@pytest.fixture
def int_widget(int_quib):
    yield ipywidgets.IntSlider(value=int_quib, min=0, max=10, step=1)


@pytest.fixture
def quib():
    return iquib(7.)


@pytest.fixture
def int_quib():
    return iquib(7)


@pytest.fixture
def func():
    return mock.Mock()


@pytest.fixture
def no_timer():
    with UNDO_GROUP_TIME.temporary_set(None):
        yield


def test_ipywidgets_ok_on_non_quibs(func):
    w = ipywidgets.FloatSlider(10.)
    w.observe(func, 'value')
    func.assert_not_called()
    w.value = 11.
    func.assert_called_once()
    assert func.mock_calls[0].args[0]['new'] == 11.
    w.value = 12.
    assert func.mock_calls[1].args[0]['new'] == 12.


def test_ipywidgets_initiate_with_quib_value(widget, quib):
    assert widget.value == quib.get_value()


def test_ipywidgets_update_when_quib_change(widget, quib):
    quib.assign(8)
    assert widget.value == 8.

    quib.assign(9)
    assert widget.value == 9.


def test_quib_is_not_overridden_upon_widget_initiation(quib):
    assert not quib.handler.is_overridden, "sanity"
    w = ipywidgets.FloatSlider(value=quib)
    assert not quib.handler.is_overridden


def test_quib_value_is_refreshed_upon_widget_change(widget, quib, no_timer):
    assert quib.get_value() == 7., "sanity"

    widget.value = 8.
    assert quib.get_value() == 8
    simulate_time_delay(widget)



def test_quib_is_only_overridden_once_per_widget_change(widget, quib, no_timer):
    assert len(quib.handler.overrider) == 0, "sanity"

    widget.value = 8.
    assert len(quib.handler.overrider) == 1
    simulate_time_delay(widget)


def test_quib_is_only_invalidated_once_per_widget_change(widget, quib, no_timer):
    assert len(quib.handler.overrider) == 0, "sanity"

    with count_invalidations(quib) as count:
        widget.value = 8.

    assert count.count == 1
    simulate_time_delay(widget)


def test_widget_sets_an_in_between_value(widget, quib, no_timer):
    widget.value = 8.7
    assert quib.get_value() == 9
    assert widget.value == 9.
    simulate_time_delay(widget)


def test_slider_value_rounding(no_timer):
    a = iquib(1.)
    b = 5 * a
    w = ipywidgets.FloatSlider(value=b)
    w.value = 32.7
    assert a.get_value() == 6.54  # without tolerance-rounding, we get 32.8 / 5 -> 6.540000000000001
    simulate_time_delay(w)


def test_tuple_quib_as_widget_value(no_timer):
    a = iquib((1., 5.))
    w = ipywidgets.FloatRangeSlider(value=a)

    w.value = [5., 9.]
    assert a.get_value() == (5., 9.)
    simulate_time_delay(w)


def test_list_quib_as_widget_value(no_timer):
    a = iquib([1., 5.])
    w = ipywidgets.FloatRangeSlider(value=a)

    w.value = [5., 9.]
    assert a.get_value() == [5., 9.]
    simulate_time_delay(w)


def test_list_of_quibs_as_widget_value(no_timer):
    a = iquib(1.)
    b = iquib(4.)
    w = ipywidgets.FloatRangeSlider(value=[a, b])

    w.value = (2., 6.)
    assert b.get_value() == 6.
    assert a.get_value() == 2.
    simulate_time_delay(w)


def test_ipywidgets_undo_redo(widget, quib, no_timer):
    project = Project.get_or_create()
    widget.value = 8.
    assert quib.get_value() == 8.
    project.undo()
    assert quib.get_value() == 7.
    project.redo()
    assert quib.get_value() == 8.
    project.undo()
    simulate_time_delay(widget)


def test_ipywidgets_aggregate_undo_redo(widget, quib, no_timer):
    project = Project.get_or_create()
    widget.value = 6.
    assert quib.get_value() == 6.
    widget.value = 5.
    assert quib.get_value() == 5.

    # A new undo group is created if the widget is delayed for longer than UNDO_GROUP_TIME
    simulate_time_delay(widget)

    widget.value = 4.
    assert quib.get_value() == 4.
    widget.value = 3.
    assert quib.get_value() == 3.

    project.undo()
    assert quib.get_value() == 5.

    project.undo()
    assert quib.get_value() == 7.

    simulate_time_delay(widget)


def test_ipywidgets_restrict_steps(widget, quib):
    widget.step = 5
    quib.assign(10)
    assert widget.value == 10
    assert quib.get_value() == 10
    with pytest.raises(ValueError):
        quib.assign(8)
    assert quib.get_value() == 8
    assert widget.value == 10
    widget.step = 1


def test_ipywidgets_and_graphics(int_widget, no_timer, int_quib, create_axes_mouse_press_move_release_events, axes):
    axes.set_xlim(0, 10)
    axes.set_ylim(0, 10)
    axes.plot(int_quib, int_quib, 'o')
    create_axes_mouse_press_move_release_events(((7, 7), (5, 5)))
    assert int_quib.get_value() == 5
