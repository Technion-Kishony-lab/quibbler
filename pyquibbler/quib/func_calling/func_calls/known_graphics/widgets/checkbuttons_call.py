import functools

from matplotlib.widgets import CheckButtons

from pyquibbler.path import PathComponent
from .widget_call import WidgetQuibFuncCall


class CheckButtonsQuibFuncCall(WidgetQuibFuncCall):

    def on_change_checkbuttons(self, widget, new_value):
        from pyquibbler.quib.quib import Quib
        actives = self.func_args_kwargs.get('actives')
        if isinstance(actives, Quib):
            buttons_checked = widget.get_status()
            labels = self.func_args_kwargs.get('labels')
            new_value_index = labels.index(new_value)
            self._inverse_assign(actives, [PathComponent(indexed_cls=list, component=new_value_index)],
                                 value=buttons_checked[new_value_index])

    def _connect_callbacks(self, widget: CheckButtons):
        widget.on_clicked(functools.partial(self.on_change_checkbuttons, widget))
