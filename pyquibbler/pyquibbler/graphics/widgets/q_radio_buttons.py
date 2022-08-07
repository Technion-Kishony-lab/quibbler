from matplotlib.axes import Axes
from matplotlib.widgets import RadioButtons
from typing import List

from pyquibbler.quib.get_value_context_manager import is_within_get_value_context


class QRadioButtons(RadioButtons):
    """
    Radio buttons we additional features:
        - They expose the selected index via the selected_index attribute
    """

    def __init__(self, ax: Axes, labels: List[str], active=0, **kwargs):
        self.created_in_get_value_context = False
        super().__init__(ax, labels, active=active, **kwargs)
        self.selected_index = active
        self.created_in_get_value_context = is_within_get_value_context()

    def set_active(self, index: int):
        if self.created_in_get_value_context:
            drawon = self.drawon
            self.drawon = False
            super().set_active(index)
            self.drawon = drawon
        else:
            super().set_active(index)
