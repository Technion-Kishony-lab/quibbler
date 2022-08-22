import pytest
import ipywidgets

from unittest import mock

from pyquibbler import iquib
from tests.integration.quib.graphics.widgets.utils import count_invalidations


@pytest.fixture
def widget():
    return ipywidgets.FloatSlider()


@pytest.fixture
def quib():
    return iquib(7.)


@pytest.fixture
def func():
    return mock.Mock()


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
    w = ipywidgets.FloatSlider(value=quib)
    assert w.value == quib.get_value()


def test_ipywidgets_update_when_quib_change(widget, quib):
    w = ipywidgets.FloatSlider(value=quib)

    quib.assign(8.)
    assert w.value == 8.

    quib.assign(9.)
    assert w.value == 9.


def test_quib_is_not_overridden_upon_widget_initiation(widget, quib):
    assert not quib.handler.is_overridden, "sanity"
    w = ipywidgets.FloatSlider(value=quib)
    assert not quib.handler.is_overridden


def test_quib_value_is_refreshed_upon_widget_change(widget, quib):
    w = ipywidgets.FloatSlider(value=quib)

    assert quib.get_value() == 7., "sanity"

    w.value = 8.
    assert quib.get_value() == 8.


def test_quib_is_only_overridden_once_per_widget_change(widget, quib):
    w = ipywidgets.FloatSlider(value=quib)

    assert len(quib.handler.overrider) == 0, "sanity"

    w.value = 8.
    assert len(quib.handler.overrider) == 1


def test_quib_is_only_invalidated_once_per_widget_change(widget, quib):
    w = ipywidgets.FloatSlider(value=quib)

    assert len(quib.handler.overrider) == 0, "sanity"

    with count_invalidations(quib) as count:
        w.value = 8.

    assert count.count == 1

