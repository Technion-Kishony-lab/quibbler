import dataclasses
from _weakref import ReferenceType
from typing import Optional, TYPE_CHECKING, Any

import ipywidgets as widgets


if TYPE_CHECKING:
    from pyquibbler.quib import Quib


def _create_button(label: str = '', icon: str = '',
                   width: str = '40px', height: str = '20px', **kwargs):
    return widgets.Button(description=label, icon=icon, **kwargs,
                          layout=widgets.Layout(width=width, height=height, display='flex', align_items='center'))


@dataclasses.dataclass
class QuibWidget:
    quib_ref: Optional[ReferenceType] = None
    _widget: Optional[widgets.VBox] = None

    def get_widget(self, widget_name: Optional[str] = None):
        widget = self._widget
        if widget_name is None:
            return widget
        if widget_name == 'name':
            return widget.children[0]
        if widget_name == 'assignments':
            return widget.children[1]

    @property
    def quib(self):
        return self.quib_ref()

    def refresh_name(self):
        self.get_widget('name').value = self.quib.pretty_repr

    def refresh_assignments(self):
        assignments_widgets = []
        for assignment in self.quib.handler.overrider._paths_to_assignments.values():
            assignment_text = assignment.get_pretty_path() + ' = ' + assignment.get_pretty_value()
            assignment_text_box = widgets.Textarea(assignment_text, continuous_update=False,
                                                   layout=widgets.Layout(width='200px', height='20px'))
            assignment_delete_button = _create_button(icon='minus', tooltip='click to delete line', width='30px')

            assignments_widgets.append(widgets.HBox([assignment_text_box, assignment_delete_button]))

        self.get_widget('assignments').children = assignments_widgets

    def refresh(self):
        self.refresh_name()
        self.refresh_assignments()

        #    widget.observe(self._on_widget_change, names='value')

    def _on_delete_assignment(self):
        pass

    def _add_assignment(self):
        pass

    def _edit_assignment(self):
        pass

    def build_widget(self):
        save = _create_button(label='Save', width='40px')
        load = _create_button(label='Load', width='40px')
        add = _create_button(icon='plus', width='30px', tooltip='click to add a new line')

        name = widgets.Label(value='')

        assignments = widgets.VBox([])

        save_load = widgets.HBox([save, load], layout=widgets.Layout(width='204px'))
        buttons = widgets.HBox([save_load, add])

        widget = widgets.VBox([name,
                               assignments,
                               buttons])

        self._widget = widget
