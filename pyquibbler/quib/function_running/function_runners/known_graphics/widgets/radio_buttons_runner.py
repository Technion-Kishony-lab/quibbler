from matplotlib.widgets import RadioButtons

from pyquibbler.quib.function_running.function_runners.known_graphics.widgets.widget_runner import WidgetRunner


class RadioButtonsRunner(WidgetRunner):

    def _on_clicked(self, new_value):
        from pyquibbler.quib import Quib
        active = self.func_call.args_values.get('active')
        if isinstance(active, Quib):
            active.assign_value(self.func_call.args_values.get('labels').index(new_value))

    def _connect_callbacks(self, widget: RadioButtons):
        widget.on_clicked(self._on_clicked)
