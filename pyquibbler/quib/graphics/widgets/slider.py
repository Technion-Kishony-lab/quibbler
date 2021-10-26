from matplotlib.widgets import Slider

from pyquibbler.quib import Quib
from pyquibbler.quib.utils import quib_method

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib


class SliderGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a slider. Will automatically add a listener and update the relevant quib
    """
    WIDGET_CLS = Slider

    def _on_change(self, new_value: float):
        val = self._get_all_args_dict().get('valinit')
        if isinstance(val, Quib):
            val.assign_value(new_value)
        else:
            # We only need to invalidate children if we didn't assign
            self.invalidate_and_redraw_at_path()

    def _call_func(self, valid_path):
        slider = super()._call_func(None)
        slider.on_changed(self._on_change)
        return slider

    @property
    @quib_method
    def val(self):
        return self.get_value().val
