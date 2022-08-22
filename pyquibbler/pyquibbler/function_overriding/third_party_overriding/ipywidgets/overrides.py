from __future__ import annotations

import functools
import contextlib

from pyquibbler.quib.quib import Quib
from typing import Dict, Optional, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    # noinspection PyPackageRequirements
    import ipywidgets
    # noinspection PyPackageRequirements
    from traitlets import TraitType


TRAIT_TO_QUIBY_WIDGET_ATTR = '_quibbler_trait_to_quiby_widget'


def is_ipywidgets_installed() -> bool:
    try:
        # noinspection PyPackageRequirements
        import ipywidgets
        # noinspection PyPackageRequirements
        import traitlets
    except ImportError:
        return False

    return True


def _bare_set(widget, trait, value):
    """ The snippet from TraitType.set that does the bare set of the trait"""
    widget._trait_values[trait] = value


def _get_or_create_trait_to_quiby_widget_trait(widget) -> Dict:
    if not hasattr(widget, TRAIT_TO_QUIBY_WIDGET_ATTR):
        setattr(widget, TRAIT_TO_QUIBY_WIDGET_ATTR, {})

    return getattr(widget, TRAIT_TO_QUIBY_WIDGET_ATTR)


class QuibyWidgetTrait:
    original_set: Optional[Callable] = None

    def __init__(self, quib: Quib, trait: TraitType, widget: ipywidgets.Widget):
        self.quib = quib
        self.trait = trait
        self.widget = widget
        self._within_quib_set: bool = False

    @contextlib.contextmanager
    def within_quib_set_context(self):
        if self._within_quib_set:
            yield
        else:
            self._within_quib_set = True
            try:
                yield
            finally:
                self._within_quib_set = False

    @staticmethod
    def get_widgets_requiring_tolerance_assignment():
        # noinspection PyPackageRequirements
        import ipywidgets
        return {
            ipywidgets.FloatSlider,
            ipywidgets.FloatRangeSlider,
        }

    def _on_widget_change(self, change):
        if not self._within_quib_set:
            new_value = change['new']
            self.quib.assign(new_value)

    def _on_quib_change(self, value):
        with self.within_quib_set_context():
            QuibyWidgetTrait.original_set(self.trait, self.widget, value)

    def set_widget_to_update_quib_upon_change(self):
        # TODO: Implement push to undo/redo on mouse drop.
        #  We will need for this to get mouse release from the widget, possibly using:
        #  w = ipyevents.Event(source=widget, watched_events=['mouseup'])
        #  w.on_dom_event(on_drop)
        self.widget.observe(self._on_widget_change, self.trait.name)

    def set_quib_to_update_widget_upon_change(self):
        self.quib.add_callback(self._on_quib_change)


def get_wrapper_for_trait_type_set():

    # noinspection PyPackageRequirements
    from traitlets import TraitType
    QuibyWidgetTrait.original_set = TraitType.set

    @functools.wraps(QuibyWidgetTrait.original_set)
    def quiby_set(self, obj, value):
        if isinstance(value, Quib):
            # We cannot call original_set because it buffers future update to the quib.
            _bare_set(obj, self.name, value.get_value())

            manager = QuibyWidgetTrait(quib=value, trait=self, widget=obj)
            manager.set_widget_to_update_quib_upon_change()
            manager.set_quib_to_update_widget_upon_change()

            trait_to_quiby_widget_trait = _get_or_create_trait_to_quiby_widget_trait(obj)
            trait_to_quiby_widget_trait[self.name] = manager
        else:
            QuibyWidgetTrait.original_set(self, obj, value)

    return quiby_set


def override_ipywidgets_if_installed():
    if not is_ipywidgets_installed():
        return

    # noinspection PyPackageRequirements
    from traitlets import TraitType

    TraitType.set = get_wrapper_for_trait_type_set()
