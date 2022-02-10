from matplotlib.widgets import RadioButtons

from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.widget_call import WidgetQuibFuncCall


class RadioButtonsQuibFuncCall(WidgetQuibFuncCall):

    def _on_clicked(self, new_value):
        from pyquibbler.quib import Quib
        active = self.args_values.get('active')
        if isinstance(active, Quib):
            active.assign(self.args_values.get('labels').index(new_value))

    def _connect_callbacks(self, widget: RadioButtons):
        widget.on_clicked(self._on_clicked)
