from matplotlib.widgets import TextBox

from pyquibbler.quib import Quib
from .widget_call import WidgetQuibFuncCall


class TextBoxQuibFuncCall(WidgetQuibFuncCall):

    def _on_change(self, new_value: float):
        val = self.args_values.get('initial')
        if isinstance(val, Quib):
            self._inverse_assign(val, [], new_value)

    def _connect_callbacks(self, widget: TextBox):
        widget.on_submit(self._on_change)
