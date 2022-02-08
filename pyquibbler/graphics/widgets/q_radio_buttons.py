from matplotlib.axes import Axes
from matplotlib.widgets import RadioButtons
from typing import List


class QRadioButtons(RadioButtons):
    """
    Radio buttons we additional features:
        - They expose the selected index via the selected_index attribute
    """

    def __init__(self, ax: Axes, labels: List[str], active=0, **kwargs):
        super().__init__(ax, labels, active=active, **kwargs)
        self.selected_index = active

    def set_active(self, index: int):
        self.selected_index = index
        super().set_active(index)
