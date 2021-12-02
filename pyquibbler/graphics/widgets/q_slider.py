from matplotlib.widgets import Slider


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
        self._drag_active = value
        if value is False and self.on_release:
            self.on_release()
