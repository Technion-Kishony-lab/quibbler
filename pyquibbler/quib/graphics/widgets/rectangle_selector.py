from contextlib import contextmanager
from dataclasses import dataclass, field
from threading import RLock
from typing import Any, Optional, List, Callable, Tuple, Mapping

from matplotlib.widgets import RectangleSelector

from pyquibbler import timer, CacheBehavior
from pyquibbler.logger import logger
from pyquibbler.quib.utils import quib_method
from pyquibbler.utils import Mutable
from .drag_context_manager import dragging, releasing

from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib

from pyquibbler.quib import Quib
from ...assignment import PathComponent


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
        self.changed_callback = None
        if interactive is None:
            interactive = True
        if onselect is None:
            onselect = lambda *args, **kwargs: None
        super().__init__(ax, onselect, interactive=interactive, **kwargs)
        self.allow_resize = allow_resize
        if extents is not None:
            self.extents = extents
        self._should_deactivate_after_release = False
        self.release_callback = None

    def set_should_deactivate_after_release(self):
        self._should_deactivate_after_release = True

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

                if self._should_deactivate_after_release:
                    self.set_active(False)
                    self.set_visible(False)
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


class RectangleSelectorGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a rectangle selector. Will automatically add a listener and update the relevant quib
    """
    WIDGET_CLS = RectangleSelector

    def __init__(self, func: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any],
                 cache_behavior: Optional[CacheBehavior]):
        super().__init__(func, args, kwargs, cache_behavior)
        self._last_extents_change = None

    def _widget_is_attempting_to_resize_when_not_allowed(self, extents):
        """
        There is a bug in the matplotlib widget that causes it to sometimes give incorrect extents,
        and attempt to resize even when the user did not request to resize- we here check if the widget attempted to
        resize when it should not have been able to
        """
        init_val = self._get_args_values().get('extents')
        allow_resize = self._get_args_values().get('allow_resize')
        if isinstance(init_val, Quib):
            previous_value = init_val.get_value()
        else:
            previous_value = self.get_value().extents

        return not allow_resize and (
                previous_value[1] - previous_value[0] != extents[1] - extents[0] or
                previous_value[3] - previous_value[2] != extents[3] - extents[2]
        )

    def _on_changed(self, extents):
        self._last_extents_change = extents
        init_val = self._get_args_values().get('extents')

        with timer("selector_change", lambda x: logger.info(f"selector change {x}")):
            if isinstance(init_val, Quib):
                if self._widget_is_attempting_to_resize_when_not_allowed(extents):
                    return
                init_val[:] = extents
            else:
                # We only need to invalidate children if we didn't assign
                self.invalidate_and_redraw_at_path()

    def _on_release(self):
        if self._last_extents_change:
            # we unfortunately ALSO need this concept of releasing because _on_release can be called while still within
            # dragging (this appears to be matplotlib internal implementation)
            # By saying `releasing` we ensure this will be recorded for undo/redo
            with releasing():
                self._on_changed(self._last_extents_change)
            self._last_extents_change = None

    def _call_func(self, valid_path: Optional[List[PathComponent]]) -> Any:
        selector = super()._call_func(None)
        selector.changed_callback = self._on_changed
        selector.release_callback = self._on_release
        return selector

    @property
    @quib_method
    def extents(self):
        return self.get_value().extents
