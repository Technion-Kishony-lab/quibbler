from matplotlib.axes import Axes
from matplotlib.widgets import RadioButtons
from typing import List, Optional, Any

from pyquibbler.quib import Quib
from pyquibbler.quib.utils import quib_method

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib
from ...assignment import PathComponent


class QRadioButtons(RadioButtons):
    """
    Radio buttons we additional features:
        - They expose the selected index via the selected_index attribute
    """

    def __init__(self, ax: Axes, labels: List[str], active=0):
        super().__init__(ax, labels, active=active)
        self.selected_index = active

    def set_active(self, index: int):
        self.selected_index = index
        super().set_active(index)


class RadioButtonsGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a matplotlib.widgets.RadioButtons. Will automatically add a listener and update the
    relevant quib
    """
    WIDGET_CLS = RadioButtons
    REPLACEMENT_CLS = QRadioButtons

    def _on_change(self, new_value: str):
        valindex = self._get_args_values().get('active')
        if isinstance(valindex, Quib):
            valindex.assign_value(self._get_args_values().get('labels').index(new_value))
        else:
            # We only need to invalidate children if we didn't assign
            self.invalidate_and_redraw_at_path()

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        radiobuttons = super()._call_func(None)
        radiobuttons.on_clicked(self._on_change)
        return radiobuttons

    @property
    @quib_method
    def value_selected(self):
        return self.get_value().value_selected

    @property
    @quib_method
    def selected_index(self):
        return self.get_value().selected_index
