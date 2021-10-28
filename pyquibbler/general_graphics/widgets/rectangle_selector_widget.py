from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from matplotlib.widgets import RectangleSelector

from pyquibbler.utils import Mutable


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
        self.changed_callback = None
        if interactive is None:
            interactive = True
        if onselect is None:
            onselect = lambda *args, **kwargs: None
        super().__init__(ax, onselect, interactive=interactive, **kwargs)
        if extents is not None:
            self.extents = extents

        selectors = getattr(ax, 'selectors', [])
        selectors.append(self)
        setattr(ax, 'selectors', selectors)

        self.changed_callback = self._on_changed

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

    def _on_changed(self, extents):
        if self.extents_quib is not None:
            self.extents_quib[:] = extents

    @property
    def extents(self):
        return super().extents

    @property
    def extents_quib(self):
        args_dict = getattr(self, '_quibbler_args_dict', {})
        return args_dict.get('extents')

    @extents.setter
    def extents(self, extents):
        super(type(self), type(self)).extents.fset(self, extents)

        if self.extents_quib is not None:
            self.extents_quib[:] = self.extents

