from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock
from typing import Any
from matplotlib.widgets import RectangleSelector

from pyquibbler.utils import Mutable

from .. import dragging
from ...quib.get_value_context_manager import is_within_get_value_context
from ...quib.graphics.redraw import skip_canvas_draws


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

    def __init__(self, ax, onselect=None, extents=None, allow_resize=True, interactive=None, **kwargs):
        self.created_in_get_value_context = False
        self.changed_callback = None
        if interactive is None:
            interactive = True
        if onselect is None:
            onselect = lambda *args, **kwargs: None
        super().__init__(ax, onselect, interactive=interactive, **kwargs)
        self.allow_resize = allow_resize
        if extents is not None:
            self.extents = extents
        self.release_callback = None
        self.created_in_get_value_context = is_within_get_value_context()

    def is_current_event_a_move_event(self):
        return 'move' in self.state or self.active_handle == 'C'

    def event_is_relevant_to_current_selector(self) -> bool:
        return (self.active_handle and self.active_handle != 'C') or self.is_current_event_a_move_event()

    def _onmove(self, event):
        if self.event_is_relevant_to_current_selector():
            if self.allow_resize or self.is_current_event_a_move_event():
                with self.CURRENT_SELECTOR.unlock() as current_selector:
                    if current_selector.val is None or current_selector.val is self:
                        current_selector.val = self
                        with dragging():
                            return super()._onmove(event)

    def _release(self, event):
        with self.CURRENT_SELECTOR.unlock() as current_selector:
            if self.event_is_relevant_to_current_selector() and current_selector.val is self:
                release_result = super()._release(event)
                current_selector.val = None

                if self.release_callback:
                    self.release_callback()
                return release_result

    @property
    def extents(self):
        return super().extents

    @extents.setter
    def extents(self, extents):
        super(type(self), type(self)).extents.fset(self, extents)
        if self.changed_callback is not None:
            # Important to use self.extents and not extents because it sorts the coordinates
            self.changed_callback(self.extents)

    def set_extents_without_callback(self, extents):
        super(type(self), type(self)).extents.fset(self, extents)

    def update(self):
        with skip_canvas_draws(should_skip=self.created_in_get_value_context):
            super().update()
