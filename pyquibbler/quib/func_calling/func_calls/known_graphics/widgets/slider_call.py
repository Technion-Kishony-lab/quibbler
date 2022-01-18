from matplotlib.widgets import Slider

from pyquibbler.graphics.widgets import QSlider
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.widget_call import WidgetQuibFuncCall


class SliderQuibFuncCall(WidgetQuibFuncCall):

    def _on_change_slider(self, new_value):
        from pyquibbler.quib.quib import Quib
        val = self.args_values.get('valinit')
        if isinstance(val, Quib):
            val.assign_value(new_value)

    def _connect_callbacks(self, widget: QSlider):
        widget.on_changed(self._on_change_slider)
        widget.on_release = self._on_change_slider
