from matplotlib.axes import Axes
from matplotlib.widgets import RadioButtons
from typing import List

from .base_q_widget import QWidget


class QRadioButtons(QWidget, RadioButtons):
    """
    Like Radio buttons, also featuring:
        - Exposing selected index via the selected_index attribute
    """

    def __init__(self, ax: Axes, labels: List[str], active=0, **kwargs):
        self.selected_index = active
        super().__init__(ax, labels, active=active, **kwargs)

    def set_active(self, index: int):
        self.selected_index = index
        with self.avoid_redraws_if_created_in_get_value_context():
            super().set_active(index)
