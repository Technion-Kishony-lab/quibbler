from numbers import Number

from matplotlib.widgets import Slider

from pyquibbler.assignment.rounding import round_to_num_digits
from pyquibbler.quib.get_value_context_manager import is_within_get_value_context


class QSlider(Slider):
    """
    Like Slider but with:
    * on_release
    * rounding step_value

    """
    def __init__(self, ax, label, valmin, valmax, valinit, **kwargs):
        self.created_in_get_value_context = False
        self.on_release = None
        self._drag_active = False
        super().__init__(ax, label, valmin, valmax, valinit, **kwargs)
        self.created_in_get_value_context = is_within_get_value_context()

    @property
    def drag_active(self):
        return self._drag_active

    @drag_active.setter
    def drag_active(self, value):
        if self._drag_active is value:
            return
        self._drag_active = value
        if not value and self.on_release:
            self.on_release(self.val)

    def _stepped_value(self, val):
        """Return *val* coerced to closest number in the ``valstep`` grid."""

        val = super()._stepped_value(val)

        if isinstance(self.valstep, Number):
            val = round_to_num_digits(val, 15)  # prevents values like 1.0000000000001

        return val

    def set_val(self, val):
        if self.created_in_get_value_context:
            drawon = self.drawon
            self.drawon = False
            super().set_val(val)
            self.drawon = drawon
        else:
            super().set_val(val)
