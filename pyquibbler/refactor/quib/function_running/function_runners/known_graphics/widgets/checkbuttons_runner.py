import functools

from matplotlib.widgets import CheckButtons

from pyquibbler.refactor.path import PathComponent
from .widget_runner import WidgetRunner


class CheckButtonsRunner(WidgetRunner):

    def on_change_checkbuttons(self, widget, new_value):
        from pyquibbler import Assignment
        from pyquibbler.refactor.quib.quib import Quib
        actives = self.func_call.args_values.get('actives')
        if isinstance(actives, Quib):
            buttons_checked = widget.get_status()
            labels = self.func_call.args_values.get('labels')
            new_value_index = labels.index(new_value)
            actives.assign(Assignment(value=buttons_checked[new_value_index],
                                      path=[PathComponent(indexed_cls=list, component=new_value_index)]))

    def _connect_callbacks(self, widget: CheckButtons):
        widget.on_clicked(functools.partial(self.on_change_checkbuttons, widget))


