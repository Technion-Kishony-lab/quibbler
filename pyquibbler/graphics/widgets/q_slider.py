from matplotlib.widgets import Slider

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
