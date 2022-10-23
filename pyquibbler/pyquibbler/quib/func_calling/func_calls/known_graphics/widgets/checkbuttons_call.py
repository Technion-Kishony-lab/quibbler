import functools
from typing import Optional

from matplotlib.widgets import CheckButtons

from pyquibbler.path import PathComponent
from .widget_call import WidgetQuibFuncCall


class CheckButtonsQuibFuncCall(WidgetQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        return 'actives'

    def on_change_checkbuttons(self, widget, new_value):
        from pyquibbler.quib.quib import Quib
        actives = self.func_args_kwargs.get('actives')
        buttons_checked = widget.get_status()
        labels = self.func_args_kwargs.get('labels')
        new_value_index = labels.index(new_value)
        if isinstance(actives, Quib):
            self._inverse_assign(actives, [PathComponent(new_value_index)],
                                 value=buttons_checked[new_value_index])
        elif isinstance(actives[new_value_index], Quib):
            self._inverse_assign(actives[new_value_index], [],
                                 value=buttons_checked[new_value_index])

    def _connect_callbacks(self, widget: CheckButtons):
        widget.on_clicked(functools.partial(self.on_change_checkbuttons, widget))
