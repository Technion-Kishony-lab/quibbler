import contextlib

from matplotlib.widgets import Widget

from pyquibbler.quib.get_value_context_manager import is_within_get_value_context


class QWidget(Widget):

    def __init__(self, *args, **kwargs):
        self.created_in_get_value_context = False
        super().__init__(*args, **kwargs)
        self.created_in_get_value_context = is_within_get_value_context()

    @contextlib.contextmanager
    def avoid_redraws_if_created_in_get_value_context(self):
        if self.created_in_get_value_context:
            drawon = self.drawon
            self.drawon = False
            try:
                yield
            finally:
                self.drawon = drawon
        else:
            yield
