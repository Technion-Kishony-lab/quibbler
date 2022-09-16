import pytest

import ipywidgets

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
        return quib_widget._assignments_box.children[index].children[0]

    return _get


@pytest.fixture
def get_assignment_delete(quib_widget):
    def _get(index: int) -> ipywidgets.Button:
        return quib_widget._assignments_box.children[index].children[1]

    return _get


def test_iquib_creates_widget(quib, quib_widget):
    assert isinstance(quib_widget, QuibWidget)


def test_widget_names_refresh_when_quib_name_changes(quib, quib_widget, child, child_widget):
    child._repr_html_()

    assert quib_widget._name_label.value == 'quib = iquib(1)'
    assert child.handler._widget._name_label.value == 'child = quib + 2'

    quib.assigned_name = 'new_quib'
    assert quib_widget._name_label.value == 'new_quib = iquib(1)'
    assert child_widget._name_label.value == 'child = new_quib + 2'


@pytest.mark.skip
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

    a0 = quib[0]
    a0.get_value()
    a1 = quib[1]
    a1.get_value()
    a2 = quib[2]
    a2.get_value()

    assert a0.cache_status is CacheStatus.ALL_VALID
    assert a1.cache_status is CacheStatus.ALL_VALID
    assert a2.cache_status is CacheStatus.ALL_VALID

    get_assignment_text(1).value = '[2] = 101'

    assert a0.cache_status is CacheStatus.ALL_VALID
    assert a2.cache_status is CacheStatus.ALL_INVALID
    assert a1.cache_status is CacheStatus.ALL_INVALID


def test_quib_widget_add_assignment(quib, quib_widget, get_assignment_text):
    quib_widget._plus_button.click()
    get_assignment_text(0).value = '{"name": "lion", "age": 7}'
    assert quib.get_value() == {"name": "lion", "age": 7}


def test_quib_widget_add_and_delete_assignment(quib, quib_widget, get_assignment_delete):
    quib_widget._plus_button.click()
    get_assignment_delete(0).click()
    assert quib.get_value() == 1


def test_quib_widget_delete_assignment(quib, quib_widget, get_assignment_delete):
    quib.assign([0, 1, 2])
    quib[1] = 10
    quib[2] = 20

    assert quib.get_value() == [0, 10, 20], "sanity"

    get_assignment_delete(1).click()
    assert quib.get_value() == [0, 1, 20]


def test_quib_widget_shows_value(quib, quib_widget):
    assert quib_widget._value_html is None
    quib_widget._value_button.value = True
    assert quib_widget._value_html.value == '''<p style="font-family:'Courier New'">1</p>'''


def test_quib_widget_shows_value_exception(quib, child, child_widget):
    child_widget._value_button.value = True
    assert child_widget._value_html.value == '''<p style="font-family:'Courier New'">3</p>'''

    quib.assign(['cannot add'])
    assert child_widget._value_html.value == 'EXCEPTION DURING GET_VALUE()'

    quib.assign(7)
    assert child_widget._value_html.value == '''<p style="font-family:'Courier New'">9</p>'''


def test_quib_widget_shows_props(quib, quib_widget):
    quib_widget._props_button.click()
