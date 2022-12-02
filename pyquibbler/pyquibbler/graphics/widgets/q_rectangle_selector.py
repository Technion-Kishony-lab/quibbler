from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import RectangleSelector
from pyquibbler.graphics.widgets.utils import prevent_squash

from pyquibbler.utilities.basic_types import Mutable
from pyquibbler.utilities.decorators import squash_recursive_calls

from pyquibbler.quib.get_value_context_manager import is_within_get_value_context


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
        return 'move' in self._state or self._active_handle == 'C'

    def event_is_relevant_to_current_selector(self) -> bool:
        return (self._active_handle and self._active_handle != 'C') or self.is_current_event_a_move_event()

    @squash_recursive_calls(prevent_squash=prevent_squash)
    def _onmove(self, event):
        if self.event_is_relevant_to_current_selector():
            if self.allow_resize or self.is_current_event_a_move_event():
                with self.CURRENT_SELECTOR.unlock() as current_selector:
                    if current_selector.val is None or current_selector.val is self:
                        current_selector.val = self
                        return super()._onmove(event)

    def _press(self, event):
        # we ignore RIGHT click as it is reserved for resetting to default:
        if event.button is MouseButton.RIGHT:
            return

        # we are not calling the super method because it resets the widget if
        # the mouse event is not close to the handles.
        # Instead, just run the part from super that check for handle selection:
        if self._interactive and self._selection_artist.get_visible():
            self._set_active_handle(event)
            self._extents_on_press = self.extents
        else:
            self._active_handle = None

    def _release(self, event):
        # we ignore RIGHT click as it is reserved for resetting to default:
        if event.button is MouseButton.RIGHT:
            return

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
        if self.created_in_get_value_context:
            extents = sorted(extents[:2]) + sorted(extents[2:])
            if self.changed_callback is not None:
                self.changed_callback(extents)
        else:
            super(type(self), type(self)).extents.fset(self, extents)

    def update(self):
        if not self.created_in_get_value_context:
            super().update()
