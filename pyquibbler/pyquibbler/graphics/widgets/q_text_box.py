from matplotlib.widgets import TextBox

from pyquibbler.quib.graphics.redraw import redraw_canvas


class QTextBox(TextBox):
    """
    Like TextBox, also featuring:
    - text does not need to be a str. If text is not str, it is converted to str and then converted back to original
      type for callback functions.
    """

    def __init__(self, ax, label, initial, **kwargs):
        self._type = type(initial)
        initial = str(initial)
        super().__init__(ax, label, initial, **kwargs)

    def convert_text_to_original_type(self, text):
        return self._type(text)

    def on_text_change(self, func):
        super().on_text_change(lambda text: func(self.convert_text_to_original_type(text)))

    def on_submit(self, func):
        super().on_submit(lambda text: func(self.convert_text_to_original_type(text)))

    def _rendercursor(self):
        # Matplotlib has a bug - does not update on MacOSX. To fix, we run our own redraw_canvas:
        super()._rendercursor()
        redraw_canvas(self.ax.figure.canvas)
