from numbers import Number

from matplotlib.widgets import Slider

from pyquibbler.assignment.assignment_template import round_to_num_digits
from pyquibbler.graphics.drag_context_manager import enter_dragging, exit_dragging, releasing


class QSlider(Slider):
    def __init__(self, ax, label, valmin, valmax, valinit, **kwargs):
        self.on_release = None
        self._drag_active = False
        super().__init__(ax, label, valmin, valmax, valinit, **kwargs)

    @property
    def drag_active(self):
        return self._drag_active

    @drag_active.setter
    def drag_active(self, value):
        if self._drag_active is value:
            return
        self._drag_active = value
        if value:
            enter_dragging()
        else:
            if self.on_release:
                with releasing():
                    self.on_release(self.val)
            exit_dragging()

    def _stepped_value(self, val):
        """Return *val* coerced to closest number in the ``valstep`` grid."""

        val = super()._stepped_value(val)

        if isinstance(self.valstep, Number):
            val = round_to_num_digits(val, 15)  # prevents values like 1.0000000000001

        return val
