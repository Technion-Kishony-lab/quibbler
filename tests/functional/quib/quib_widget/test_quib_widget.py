import ipywidgets
import numpy as np
import pytest

from pyquibbler import iquib, CacheStatus
from pyquibbler.ipywidget_viewer.quib_widget import QuibWidget, WidgetQuibDeletedException


@pytest.fixture
def quib():
    quib = iquib(1, assigned_name='quib')
    quib._repr_html_()
    return quib


@pytest.fixture
def child(quib):
    child = quib + 2
    child.assigned_name = 'child'
    child.allow_overriding = True
    child._repr_html_()
    return child


@pytest.fixture
def quib_widget(quib) -> QuibWidget:
    return quib.handler._widget


@pytest.fixture
def child_widget(child) -> QuibWidget:
    return child.handler._widget


@pytest.fixture
def get_assignment_text(quib_widget):

    def _get(index: int) -> ipywidgets.Text:
        return quib_widget._get_assignment_widget().children[index].children[0]

    return _get


@pytest.fixture
def get_assignment_delete(quib_widget):

    def _get(index: int) -> ipywidgets.Button:
        return quib_widget._get_assignment_widget().children[index].children[1]

    return _get


def test_iquib_creates_widget(quib, quib_widget):
    assert isinstance(quib_widget, QuibWidget)


def test_quib_without_overridding_does_not_create_widget(quib):
    quib.allow_overriding = False
    assert quib._repr_html_() is None


def test_widget_names_refresh_when_quib_name_changes(quib, quib_widget, child, child_widget):
    child.allow_overriding = True  # so that it create a QuibWidget
    child._repr_html_()

    assert quib_widget._get_name_widget().value == 'quib = iquib(1)'
    assert child.handler._widget._get_name_widget().value == 'child = quib + 2'

    quib.assigned_name = 'new_quib'
    assert quib_widget._get_name_widget().value == 'new_quib = iquib(1)'
    assert child_widget._get_name_widget().value == 'child = new_quib + 2'


def test_widget_disabled_when_quib_deleted():
    a = iquib(1)
    a._repr_html_()
    widget = a.handler._widget
    with pytest.raises(WidgetQuibDeletedException, match='.*'):
        del a
        widget.quib


def test_quib_widget_adds_assignments(quib, quib_widget, get_assignment_text):
    quib.assign([0, 1, 2])
    assert get_assignment_text(0).value == '= [0, 1, 2]'

    quib[2] = 20
    assert get_assignment_text(1).value == '[2] = 20'


def test_quib_widget_updates_quib_upon_assignment_edit(quib, quib_widget, get_assignment_text):
    quib.assign([0, 1, 2])
    quib[2] = 20

    get_assignment_text(1).value = '[1] = "wow"'
    assert quib.get_value() == [0, 'wow', 2]


def test_quib_widget_update_only_invalidates_old_and_new_path(quib, quib_widget, get_assignment_text):
    quib.assign([0, 1, 2])
    quib[1] = 100

    a0 = quib[0]; a0.get_value()
    a1 = quib[1]; a1.get_value()
    a2 = quib[2]; a2.get_value()

    assert a0.cache_status is CacheStatus.ALL_VALID
    assert a1.cache_status is CacheStatus.ALL_VALID
    assert a2.cache_status is CacheStatus.ALL_VALID

    get_assignment_text(1).value = '[2] = 101'

    assert a0.cache_status is CacheStatus.ALL_VALID
    assert a2.cache_status is CacheStatus.ALL_INVALID
    assert a1.cache_status is CacheStatus.ALL_INVALID


def test_quib_widget_add_assignment(quib, quib_widget, get_assignment_text):
    quib_widget._get_add_button_widget().click()
    get_assignment_text(0).value = '{"name": "lion", "age": 7}'
    assert quib.get_value() == {"name": "lion", "age": 7}


def test_quib_widget_add_and_delete_assignment(quib, quib_widget, get_assignment_delete):
    quib_widget._get_add_button_widget().click()
    get_assignment_delete(0).click()
    assert quib.get_value() == 1


@pytest.mark.parametrize(['initial_value', 'override_text', 'final_value'], [
    ([1, 2, 3], '[1] = 0', [1, 0, 3]),
    ([1, 2, 3], '   [1] =0  ', [1, 0, 3]),
    ([1, 2, 3], ' "=0"', "=0"),
    ([1, 2, 3], ' = "wow"', "wow"),
    ([1, 2, 3], ' = array([1])', np.array([1])),
    ([1, 2, 3], ' = default', 1),  # original quib value
    ({'a': 1, 'b':[1, 2]}, " ['b'][1] = 3.14", {'a': 1, 'b':[1, 3.14]}),
])
def test_parsing_assignment_text(quib, quib_widget, get_assignment_text, initial_value, override_text, final_value):
    quib.assign(initial_value)
    quib_widget._get_add_button_widget().click()
    get_assignment_text(1).value = override_text
    assert quib.get_value() == final_value


def test_quib_widget_delete_assignment(quib, quib_widget, get_assignment_delete):
    quib.assign([0, 1, 2])
    quib[1] = 10
    quib[2] = 20

    assert quib.get_value() == [0, 10, 20],  "sanity"

    get_assignment_delete(1).click()
    assert quib.get_value() == [0, 1, 20]
