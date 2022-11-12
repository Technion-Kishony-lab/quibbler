from __future__ import annotations
from dataclasses import dataclass

from typing import Optional, Callable, Union, List, Tuple

from pyquibbler.user_utils.quiby_funcs import quiby
from pyquibbler.optional_packages.get_ipywidgets import ipywidgets as widgets

from pyquibbler.assignment.assignment_to_from_text import \
    convert_simplified_text_to_assignment, convert_assignment_to_simplified_text
from pyquibbler.exceptions import PyQuibblerException


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib
    from weakref import ReferenceType


ASSIGNMENT_TOOLTIP = '\n'.join((
    'Add assignment.',
    '',
    'To fully override, use "= value", e.g.:',
    '',
    '       = array([10, 20])',
    '',
    'or, just specify the assigned value. e.g.:',
    '',
    '       array([10, 20])',
    '',
    'To override a specific element,',
    'use assignment syntax. e.g.:',
    '',
    '       [2] = 7',
))

WIDGET_WIDTH = 280


def _create_button(label: str = '', icon: str = '',
                   width: str = 'auto', height: str = '20px', callback: Callable = None, **kwargs):
    button = widgets.Button(description=label, icon=icon, **kwargs,
                            layout=widgets.Layout(width=width, height=height, display='flex', align_items='center'))
    if callback:
        button.on_click(lambda *_: callback())

    return button


def _create_toggle_button(label: str = '', icon: str = '',
                          width: str = 'auto', height: str = '20px', callback: Callable = None, **kwargs):
    button = widgets.ToggleButton(
        description=label, icon=icon, **kwargs,
        layout=widgets.Layout(width=width, height=height, display='flex', align_items='center'))
    if callback:
        button.observe(lambda *_: callback(), names='value')

    return button


def remove_nones(itr: Union[List, Tuple]):
    return type(itr)(item for item in itr if item is not None)


@quiby(pass_quibs=True)
def html_repr(quib: Quib) -> str:
    try:
        value = quib.get_value()
        return f'''<p style="font-family:'Courier New'">{repr(value)}</p>'''
    except Exception:
        return '''<p style="color:red">EXCEPTION DURING GET_VALUE()</p>'''


class WidgetQuibDeletedException(PyQuibblerException):

    def __str__(self):
        return 'Cannot find quib. Disabling widget.'


@dataclass
class QuibWidget:
    """
    Creates and control a quib widget allowing viewing, editing and save/load of quib overrides.

    QuibWidgets are created automatically when a quib is displayed in Jupyter lab.
    """

    quib_ref: Optional[ReferenceType[Quib]] = None
    _name_label: Optional[widgets.Label] = None
    _main_box: Optional[widgets.VBox] = None
    _value_button: Optional[widgets.ToggleButton] = None
    _props_button: Optional[widgets.Button] = None
    _save_button: Optional[widgets.Button] = None
    _load_button: Optional[widgets.Button] = None
    _plus_button: Optional[widgets.Button] = None
    _assignments_button: Optional[widgets.ToggleButton] = None
    _assignments_box: Optional[widgets.VBox] = None
    _value_html: Optional[widgets.HTML] = None

    def get_widget(self):
        return self._main_box

    def show_quib_properties_as_pop_up(self):
        """
        Create a pop-up window displaying the quib's properties
        """
        from pyquibbler.optional_packages.get_IPython import display, HTML

        s = '<script type="text/Javascript">'
        s += 'var win = window.open("", "Title", "toolbar=no, location=no, directories=no, status=no, menubar=no, ' \
             'scrollbars=yes, resizable=yes, width=300, height=500, top="+(screen.height-400)+", ' \
             'left="+(screen.width-840));'
        s += 'win.document.body.innerHTML = \'' + self.quib.display_properties().get_html_repr() + '\';'
        s += '</script>'

        output = widgets.Output()
        children = self._main_box.children
        children_with_output = [*children, output]
        self._main_box.children = children_with_output
        with output:
            display(HTML(s))

        self._main_box.children = children

    @property
    def quib(self) -> Quib:
        if self.quib_ref() is None:
            self.disable_widget()
            raise WidgetQuibDeletedException()

        return self.quib_ref()

    def disable_widget(self):
        self.get_widget().children = (widgets.Label(value='OBSOLETE: ' + self._name_label.value), )

    def _save_quib(self):
        self.quib.save()

    def _load_quib(self):
        self.quib.load()

    def _toggle_show_value(self):
        if self._value_button.value:
            self._value_html = widgets.HTML(html_repr(self.quib))
        else:
            self._value_html = None
        self._refresh_items_in_widget()

    def _create_assignment_box(self, assignment_index: int, text: str = '') -> widgets.HBox:
        assignment_text_box = widgets.Text(text, continuous_update=False,
                                           description_tooltip=ASSIGNMENT_TOOLTIP,
                                           layout=widgets.Layout(width=f'{WIDGET_WIDTH}px'))  # , height='20px'
        assignment_text_box.observe(lambda change: self._on_edit_assignment(assignment_index, change), names='value')

        assignment_delete_button = _create_button(icon='minus', tooltip='Delete assignment', width='30px',
                                                  callback=lambda *_: self._on_delete_assignment(assignment_index))
        return widgets.HBox([assignment_text_box, assignment_delete_button])

    def _refresh_assignments(self):
        if self._assignments_box is None:
            return
        assignments_widgets = []
        for index, assignment in enumerate(self.quib.handler.overrider._paths_to_assignments.values()):
            assignment_text = convert_assignment_to_simplified_text(assignment)
            assignments_widgets.append(self._create_assignment_box(index, assignment_text))

        self._assignments_box.children = assignments_widgets
        self._plus_button.disabled = False

    def _refresh_save_load_button_disable_state(self):
        disabled = self.quib.handler.file_syncer.is_synced
        if self._save_button is not None:
            self._save_button.disabled = disabled
        if self._load_button is not None:
            self._load_button.disabled = disabled

    def refresh(self):
        self._refresh_assignments()
        self._refresh_save_load_button_disable_state()

    def _on_delete_assignment(self, assignment_index: int):
        if assignment_index >= len(self.quib.handler.overrider):
            children = list(self._assignments_box.children)
            children.pop(assignment_index)
            self._assignments_box.children = children
            self._plus_button.disabled = False
        else:
            from pyquibbler import Project
            Project.get_or_create().remove_assignment_from_quib(self.quib, assignment_index)

    def _add_empty_assignment(self, *_):
        children = list(self._assignments_box.children)
        children.append(self._create_assignment_box(len(children)))
        self._assignments_box.children = children
        self._plus_button.disabled = True

    def _on_edit_assignment(self, assignment_index, change):
        override_text: str = change['new']
        assignment = convert_simplified_text_to_assignment(override_text)
        from pyquibbler import Project
        Project.get_or_create().upsert_assignment_to_quib(self.quib, assignment_index, assignment)

    def _toggle_show_overrides(self):
        if self._assignments_button.value:
            self._save_button = _create_button(label='Save', callback=self._save_quib,
                                               tooltip='Save assignments to file')

            self._load_button = _create_button(label='Load', callback=self._load_quib,
                                               tooltip='Load assignments from file')

            self._plus_button = _create_button(icon='plus', callback=self._add_empty_assignment,
                                               tooltip='Add a new assignment')
            self._assignments_box = widgets.VBox([])
        else:
            self._save_button = None
            self._load_button = None
            self._plus_button = None
            self._assignments_box = None

        self._refresh_items_in_widget()
        self._refresh_assignments()

    def build_widget(self):

        self._main_box = widgets.VBox([])

        self._name_label = widgets.Label(value=self.quib.get_quiby_name(as_repr=True))

        self._props_button = _create_button(label='Props', callback=self.show_quib_properties_as_pop_up,
                                            tooltip="Show quib's properties")

        self._value_button = _create_toggle_button(label='Value', callback=self._toggle_show_value,
                                                   tooltip="Show quib's value")

        if self.quib.allow_overriding or self.quib.handler.is_overridden:
            self._assignments_button = _create_toggle_button(label='Overrides', callback=self._toggle_show_overrides,
                                                             tooltip="Show list of overriding assignments")
            self._assignments_button.value = True
        else:
            self._refresh_items_in_widget()

    def _refresh_items_in_widget(self):
        buttons = widgets.HBox(
            remove_nones((self._value_button,
                          self._props_button,
                          self._assignments_button,
                          self._save_button,
                          self._load_button)),
            layout=widgets.Layout(width=f'{WIDGET_WIDTH + 4}px'))

        buttons = widgets.HBox(remove_nones((buttons, self._plus_button)))

        self._main_box.children = remove_nones((
            self._name_label,
            self._assignments_box,
            buttons,
            self._value_html,
        ))
