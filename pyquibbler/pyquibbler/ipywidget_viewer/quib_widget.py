from __future__ import annotations
import dataclasses
import ipywidgets as widgets

from pyquibbler.assignment import Overrider
from pyquibbler.assignment.overrider import ASSIGNMENT_VALUE_TEXT_DICT
from pyquibbler.exceptions import PyQuibblerException
from _weakref import ReferenceType
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


def _create_button(label: str = '', icon: str = '',
                   width: str = '40px', height: str = '20px', **kwargs):
    return widgets.Button(description=label, icon=icon, **kwargs,
                          layout=widgets.Layout(width=width, height=height, display='flex', align_items='center'))


class WidgetQuibDeletedException(PyQuibblerException):

    def __str__(self):
        return 'Cannot find quib. Disabling widget.'


@dataclasses.dataclass
class QuibWidget:
    """
    Creates and control a quib widget composed of several ipywidgets.
    """

    quib_ref: Optional[ReferenceType[Quib]] = None
    _widget: Optional[widgets.VBox] = None

    def get_widget(self):
        return self._widget

    def _get_name_widget(self) -> widgets.Label:
        return self._widget.children[0]

    def _get_assignment_widget(self) -> widgets.HBox:
        return self._widget.children[1]

    def _get_add_button_widget(self) -> widgets.Button:
        return self._widget.children[2].children[1]

    def _get_save_button_widget(self) -> widgets.Button:
        return self._widget.children[2].children[0].children[0]

    def _get_load_button_widget(self) -> widgets.Button:
        return self._widget.children[2].children[0].children[1]

    @property
    def quib(self) -> Quib:
        if self.quib_ref() is None:
            self.disable_widget()
            raise WidgetQuibDeletedException()

        return self.quib_ref()

    def disable_widget(self):
        self.get_widget().children = (widgets.Label(value='OBSOLETE: ' + self._get_name_widget().value),)

    def _refresh_name(self):
        self._get_name_widget().value = self.quib.pretty_repr

    def _create_assignment_box(self, assignment_index: int, text: str = '') -> widgets.HBox:
        assignment_text_box = widgets.Text(text, continuous_update=False,
                                           layout=widgets.Layout(width='200px'))  # , height='20px'
        assignment_text_box.observe(lambda change: self._on_edit_assignment(assignment_index, change), names='value')

        assignment_delete_button = _create_button(icon='minus', tooltip='click to delete line', width='30px')
        assignment_delete_button.on_click(lambda *_: self._on_delete_assignment(assignment_index), )
        return widgets.HBox([assignment_text_box, assignment_delete_button])

    def _refresh_assignments(self):
        assignments_widgets = []
        for index, assignment in enumerate(self.quib.handler.overrider._paths_to_assignments.values()):
            assignment_text = assignment.get_pretty_path() + ' = ' + assignment.get_pretty_value()
            assignments_widgets.append(self._create_assignment_box(index, assignment_text))

        self._get_assignment_widget().children = assignments_widgets
        self._get_add_button_widget().disabled = False

    def _refresh_save_load_button_disable_state(self):
        disabled = self.quib.handler.file_syncer.is_synced
        self._get_save_button_widget().disabled = disabled
        self._get_load_button_widget().disabled = disabled

    def refresh(self):
        self._refresh_name()
        self._refresh_assignments()
        self._refresh_save_load_button_disable_state()

    def _on_delete_assignment(self, assignment_index: int):
        if assignment_index >= len(self.quib.handler.overrider):
            children = list(self._get_assignment_widget().children)
            children.pop(assignment_index)
            self._get_assignment_widget().children = children
            self._get_add_button_widget().disabled = False
        else:
            from pyquibbler import Project
            Project.get_or_create().remove_assignment_from_quib(self.quib, assignment_index)

    def _add_empty_assignment(self, *_):
        widget = self._get_assignment_widget()
        children = list(widget.children)
        children.append(self._create_assignment_box(len(children)))
        widget.children = children
        self._get_add_button_widget().disabled = True

    def _on_edit_assignment(self, assignment_index, change):
        override_text: str = change['new']
        override_text = override_text.strip()

        if override_text.startswith('='):
            # '= value'
            override_text = f'quib.assign({override_text[1:]})'
        else:
            try:
                eval(override_text, ASSIGNMENT_VALUE_TEXT_DICT)
                # 'value'
                override_text = f'quib.assign({override_text})'
            except Exception:
                # 'path = value'
                override_text = f'quib{override_text}'

        overrider = Overrider()
        overrider.load_from_assignment_text(override_text)
        assignment = overrider[0]

        from pyquibbler import Project
        Project.get_or_create().upsert_assignment_to_quib(self.quib, assignment_index, assignment)

    def build_widget(self):
        save = _create_button(label='Save', width='40px')
        save.on_click(lambda *_: self.quib.save())
        load = _create_button(label='Load', width='40px')
        load.on_click(lambda *_: self.quib.load())
        add = _create_button(icon='plus', width='30px', tooltip='click to add a new line')
        add.on_click(self._add_empty_assignment)
        name = widgets.Label(value='')

        assignments = widgets.VBox([])

        save_load = widgets.HBox([save, load], layout=widgets.Layout(width='204px'))
        buttons = widgets.HBox([save_load, add])

        widget = widgets.VBox([name,
                               assignments,
                               buttons])

        self._widget = widget
