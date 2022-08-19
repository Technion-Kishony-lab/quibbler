import dataclasses
from _weakref import ReferenceType
from typing import Optional, TYPE_CHECKING

import ipywidgets as widgets


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
    quib_ref: Optional[ReferenceType] = None
    _widget: Optional[widgets.VBox] = None

    def get_widget(self):
        return self._widget

    def _get_name_widget(self) -> widgets.Label:
        return self._widget.children[0]

    def _get_assignment_widget(self) -> widgets.HBox:
        return self._widget.children[1]

    def _get_add_button_widget(self) -> widgets.Button:
        return self._widget.children[2].children[1]

    @property
    def quib(self):
        if self.quib_ref() is None:
            self.disable_widget()
            raise WidgetQuibDeletedException()

        return self.quib_ref()

    def disable_widget(self):
        self.get_widget().children = (widgets.Label(value='OBSOLETE: ' + self._get_name_widget().value),)

    def refresh_name(self):
        self._get_name_widget().value = self.quib.pretty_repr

    def _create_assignment_box(self, assignment_index: int, text: str = '') -> widgets.HBox:
        assignment_text_box = widgets.Textarea(text, continuous_update=False,
                                               layout=widgets.Layout(width='200px', height='20px'))
        assignment_delete_button = _create_button(icon='minus', tooltip='click to delete line', width='30px')
        assignment_delete_button.on_click(lambda *_: self._on_delete_assignment(assignment_index), )
        return widgets.HBox([assignment_text_box, assignment_delete_button])

    def refresh_assignments(self):
        assignments_widgets = []
        for index, assignment in enumerate(self.quib.handler.overrider._paths_to_assignments.values()):
            assignment_text = assignment.get_pretty_path() + ' = ' + assignment.get_pretty_value()
            assignments_widgets.append(self._create_assignment_box(index, assignment_text))

        self._get_assignment_widget().children = assignments_widgets
        self._get_add_button_widget().disabled = False

    def refresh(self):
        self.refresh_name()
        self.refresh_assignments()

        #    widget.observe(self._on_widget_change, names='value')

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

    def _edit_assignment(self):
        pass

    def build_widget(self):
        save = _create_button(label='Save', width='40px')
        load = _create_button(label='Load', width='40px')
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
