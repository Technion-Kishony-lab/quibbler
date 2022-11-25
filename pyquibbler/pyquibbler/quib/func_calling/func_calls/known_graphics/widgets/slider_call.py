from dataclasses import dataclass
from typing import Optional

from pyquibbler.graphics.widgets import QSlider
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.widget_call import WidgetQuibFuncCall
from pyquibbler.quib.quib import Quib


@dataclass
class SliderQuibFuncCall(WidgetQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        return 'valinit'

    def _on_change_slider(self, new_value, widget: QSlider):
        val = self.func_args_kwargs.get('valinit')
        if isinstance(val, Quib):
            tolerance = widget.get_tolerance()
            self._inverse_assign(val, [], new_value, tolerance=tolerance, on_drag=True)

    def _connect_callbacks(self, widget: QSlider):
        widget.on_changed(lambda new_value: self._on_change_slider(new_value, widget))

        # on_release is now disabled. it causes the overriding dialog to appear twice.
        # and it leads to two evaluations of randomization (e.g., in the dice demo).
        widget.on_release = self._on_release
