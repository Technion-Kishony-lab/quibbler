from __future__ import annotations

import contextlib

import numpy as np

from pyquibbler.assignment import AssignmentToQuib, get_override_group_for_quib_changes, create_assignment
from pyquibbler.quib.quib import Quib
from typing import Optional, Callable, TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyquibbler.optional_packages.get_ipywidgets import ipywidgets, TraitType


class QuibyWidgetTrait:
    original_set: Optional[Callable] = None

    def __init__(self, quib: Quib, trait: TraitType, widget: ipywidgets.Widget):
        self.quib = quib
        self.trait = trait
        self.widget = widget
        self._within_quib_set: bool = False
        self._immediately_after_quib_set = True

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

    def _on_widget_change(self, change):
        if not self._within_quib_set and not self._immediately_after_quib_set:
            new_value = change['new']
            quib_type = self.quib.get_type()
            if np.issubdtype(quib_type, np.integer):
                new_value = round(new_value)
            new_value = self.quib.get_type()(new_value)
            self._inverse_assign(value=new_value)
        else:
            self._immediately_after_quib_set = False

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

    def _inverse_assign(self, value: Any, on_drag: bool = False):
        assignment = create_assignment(value, path=[], tolerance=self.get_tolerance(value))
        get_override_group_for_quib_changes([AssignmentToQuib(self.quib, assignment)]) \
            .apply(is_dragging=on_drag)

    def get_tolerance(self, value):
        return None


class FloatSliderQuibyWidgetTrait(QuibyWidgetTrait):
    def get_tolerance(self, value):
        if isinstance(value, (list, tuple)):
            return type(value)(np.array(value) * 1e-15)
        return value * 1e-15


def get_widget_to_quiby_widget_trait() -> dict:
    from pyquibbler.optional_packages.get_ipywidgets import ipywidgets
    return {
        ipywidgets.FloatSlider: FloatSliderQuibyWidgetTrait,
        ipywidgets.FloatRangeSlider: FloatSliderQuibyWidgetTrait,
        ipywidgets.FloatLogSlider: FloatSliderQuibyWidgetTrait,
    }


def get_quiby_widget_trait_type(widget):
    return get_widget_to_quiby_widget_trait().get(type(widget), QuibyWidgetTrait)
