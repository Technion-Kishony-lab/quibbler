from matplotlib.widgets import Slider

from pyquibbler.graphics.widgets import QSlider
from pyquibbler.quib.function_running.function_runners.known_graphics.widgets.widget_runner import WidgetRunner


class SliderRunner(WidgetRunner):

    def _on_change_slider(self, new_value):
        from pyquibbler.quib.quib import Quib
        val = self.func_call.args_values.get('valinit')
        if isinstance(val, Quib):
            val.assign_value(new_value)

    def _connect_callbacks(self, widget: QSlider):
        widget.on_changed(self._on_change_slider)
        widget.on_release = self._on_change_slider
