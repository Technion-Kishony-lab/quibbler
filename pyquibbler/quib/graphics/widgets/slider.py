import contextlib
from typing import Optional, List, Any
from matplotlib.widgets import Slider

from pyquibbler.quib import Quib
from pyquibbler.quib.utils import quib_method
from .drag_context_manager import dragging

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib
from ...assignment import PathComponent


class QSlider(Slider):
    def __init__(self, ax, label, valmin, valmax, valinit, **kwargs):
        self.on_release = None
        self._drag_active = False
        self._did_set_on_change = False
        super().__init__(ax, label, valmin, valmax, valinit, **kwargs)

        # It could have seemed that another implementation would be to call `on_changed` in the init with a
        # private method and just call that with a supplied function (instead of the _did_set_on_change design)
        # It's CRITICAL not to set `on_changed` here but only when necessary, as there is a memory leak in matplotlib-
        # When calling disconnect_events() you expect anything you connected to be disconnected, but there is an
        # "observers" in the slider that does not disconnect your "on_changed" event

    @property
    def drag_active(self):
        return self._drag_active

    @drag_active.setter
    def drag_active(self, value):
        self._drag_active = value
        if value is False and self.on_release:
            self.on_release()

    def set_single_on_change(self, func):
        """
        We call this instead on_changed(...) to ensure we're only setting a callback *once*. If you call on_changed on
        the same widget multiple times,  you'll create multiple callbacks
        """
        if not self._did_set_on_change:
            self.on_changed(func)
        self._did_set_on_change = True


class SliderGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a slider. Will automatically add a listener and update the relevant quib
    """
    WIDGET_CLS = QSlider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._previous_set_value = None

    def _on_change(self, new_value: float):
        self._previous_set_value = new_value
        context = dragging() if self.get_value().drag_active else contextlib.nullcontext()
        with context:
            val = self._get_args_values().get('valinit')
            if isinstance(val, Quib):
                val.assign_value(new_value)
            else:
                # We only need to invalidate children if we didn't assign
                self.invalidate_and_redraw_at_path()

    def _on_release(self):
        if self._previous_set_value:
            self._on_change(self._previous_set_value)
            self._previous_set_value = None

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        slider = super()._call_func(None)
        slider.set_single_on_change(self._on_change)
        slider.on_release = self._on_release
        return slider

    @property
    @quib_method
    def val(self):
        return self.get_value().val
