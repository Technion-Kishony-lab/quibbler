from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import partial
from threading import RLock
from typing import Callable, Any
from matplotlib.widgets import RectangleSelector

from pyquibbler.quib.utils import quib_method
from pyquibbler.utils import Mutable

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib

from ... import Quib


@dataclass
class Locked:
    _val: Any
    _lock: RLock = field(default_factory=RLock)

    @contextmanager
    def unlock(self):
        with self._lock:
            yield self._val


class QRectangleSelector(RectangleSelector):
    CURRENT_SELECTOR = Locked(Mutable(None))

    def __init__(self, ax, onselect=None, extents=None, interactive=None, **kwargs):
        if interactive is None:
            interactive = True
        super().__init__(ax, onselect, interactive=interactive, **kwargs)
        if extents is not None:
            self.extents = extents

    def event_is_relevant_to_current_selector(self) -> bool:
        return (self.active_handle and self.active_handle != 'C') or (
            (('move' in self.state or self.active_handle == 'C')))

    def _onmove(self, event):
        if self.event_is_relevant_to_current_selector():
            with self.CURRENT_SELECTOR.unlock() as current_selector:
                if current_selector.val is None or current_selector.val is self:
                    current_selector.val = self
                    return super()._onmove(event)

    def _release(self, event):
        with self.CURRENT_SELECTOR.unlock() as current_selector:
            if self.event_is_relevant_to_current_selector() and current_selector.val is self:
                release_result = super()._release(event)
                current_selector.val = None
                return release_result


class RectangleSelectorGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a rectangle selector. Will automatically add a listener and update the relevant quib
    """
    WIDGET_CLS = RectangleSelector
    REPLACEMENT_CLS = QRectangleSelector

    def _on_select(self, user_onselect, click_event, release_event):
        if user_onselect is not None:
            user_onselect(click_event, release_event)

        val = self._all_args_dict.get('extents')
        if isinstance(val, Quib):
            raise TypeError('Quib extents are not supported yet')
            val[:] = click_event.xdata, release_event.xdata, click_event.ydata, release_event.ydata
        else:
            # We only need to invalidate children if we didn't assign
            self.invalidate_and_redraw_at_path()

    def _call_func(self):
        selector = super()._call_func()
        selector.onselect = partial(self._on_select, selector.onselect)
        return selector

    @property
    @quib_method
    def extents(self):
        return self.get_value().extents
