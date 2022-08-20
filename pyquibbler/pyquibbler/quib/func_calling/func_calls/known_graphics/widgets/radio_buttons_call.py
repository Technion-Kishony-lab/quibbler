from typing import Optional

from matplotlib.widgets import RadioButtons

from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.widget_call import WidgetQuibFuncCall


class RadioButtonsQuibFuncCall(WidgetQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        return 'active'

    def _on_clicked(self, new_value):
        from pyquibbler.quib.quib import Quib
        active = self.func_args_kwargs.get('active')
        if isinstance(active, Quib):
            self._inverse_assign(active, [], self.func_args_kwargs.get('labels').index(new_value))

    def _connect_callbacks(self, widget: RadioButtons):
        widget.on_clicked(self._on_clicked)
