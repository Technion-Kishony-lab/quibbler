import numpy as np

from pyquibbler.graphics import releasing
from pyquibbler.graphics.widgets import QRectangleSelector
from pyquibbler.logger import logger
from .widget_call import WidgetQuibFuncCall
from pyquibbler.path import PathComponent


class RectangleSelectorQuibFuncCall(WidgetQuibFuncCall):
    _last_extents_change = None

    def _widget_is_attempting_to_resize_when_not_allowed(self, extents):
        """
        There is a bug in the matplotlib widget that causes it to sometimes give incorrect extents,
        and attempt to resize even when the user did not request to resize- we here check if the widget attempted to
        resize when it should not have been able to
        """
        from pyquibbler.quib import Quib
        init_val = self.args_values.get('extents')
        allow_resize = self.args_values.get('allow_resize')
        if isinstance(init_val, Quib):
            previous_value = init_val.get_value()
        else:
            previous_value = self.run([]).extents

        return not allow_resize and (
                previous_value[1] - previous_value[0] != extents[1] - extents[0] or
                previous_value[3] - previous_value[2] != extents[3] - extents[2]
        )

    def _on_changed(self, extents):
        self._last_extents_change = extents
        init_val = self.args_values.get('extents')

        from pyquibbler import timer
        from pyquibbler.quib import Quib
        if isinstance(init_val, Quib):
            with timer("selector_change", lambda x: logger.info(f"selector change {x}")):
                if self._widget_is_attempting_to_resize_when_not_allowed(extents):
                    return
                self._inverse_assign(init_val, [PathComponent(component=slice(0, 4), indexed_cls=np.ndarray)], extents)

    def _on_release(self):
        if self._last_extents_change:
            # we unfortunately ALSO need this concept of releasing because _on_release can be called while still within
            # dragging (this appears to be matplotlib internal implementation)
            # By saying `releasing` we ensure this will be recorded for undo/redo
            with releasing():
                self._on_changed(self._last_extents_change)
            self._last_extents_change = None

    def _connect_callbacks(self, widget: QRectangleSelector):
        widget.changed_callback = self._on_changed
        widget.release_callback = self._on_release
