from typing import List

from matplotlib.widgets import TextBox

from pyquibbler.quib import Quib, PathComponent
from pyquibbler.quib.utils import quib_method

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib


class TextBoxGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a TextBox. Will automatically add a listener and update the relevant quib
    """
    WIDGET_CLS = TextBox

    def _on_change(self, new_value: float):
        val = self.get_args_values().get('initial')
        if isinstance(val, Quib):
            val.assign_value(new_value)
        else:
            # We only need to invalidate children if we didn't assign
            self.invalidate_and_redraw_at_path()

    def _call_func(self, valid_path: List[PathComponent]):
        textbox = super()._call_func(None)
        textbox.on_submit(self._on_change)
        return textbox

    @property
    @quib_method
    def val(self):
        return self.get_value().val
