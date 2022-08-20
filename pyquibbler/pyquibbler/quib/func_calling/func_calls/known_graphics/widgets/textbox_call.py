from typing import Optional

from matplotlib.widgets import TextBox

from pyquibbler.quib.quib import Quib
from .widget_call import WidgetQuibFuncCall


class TextBoxQuibFuncCall(WidgetQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        return 'initial'

    def _on_change(self, new_value: str):
        val = self.func_args_kwargs.get('initial')
        if isinstance(val, Quib):
            self._inverse_assign(val, [], new_value)

    def _connect_callbacks(self, widget: TextBox):
        widget.on_submit(self._on_change)
