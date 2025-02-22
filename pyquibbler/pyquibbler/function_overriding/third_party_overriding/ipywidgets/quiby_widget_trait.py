from __future__ import annotations

import contextlib
import numpy as np

from typing import Optional, Callable, TYPE_CHECKING, Any

from pyquibbler.utilities.basic_types import Mutable
from pyquibbler.assignment import AssignmentToQuib, get_override_group_for_quib_changes, create_assignment
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.graphics.redraw import end_dragging, start_dragging

from .denounce_timer import DebounceTimer


if TYPE_CHECKING:
    from pyquibbler.optional_packages.get_ipywidgets import ipywidgets, TraitType


UNDO_GROUP_TIME = Mutable(0.1)


class QuibyWidgetTrait:
    original_set: Optional[Callable] = None
    is_draggable: bool = True

    def __init__(self, quib: Quib, trait: TraitType, widget: ipywidgets.Widget):
        self.quib = quib
        self.trait = trait
        self.widget = widget
        self._within_quib_set: bool = False
        self._immediately_after_quib_set = True
        self._is_dragging = False
        self.denounce_timer = DebounceTimer(UNDO_GROUP_TIME.val, self.on_mouse_drop)

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
        if self._within_quib_set or self._immediately_after_quib_set:
            self._immediately_after_quib_set = False
            return

        if self.is_draggable and not self._is_dragging:
            start_dragging(id(self))
            self._is_dragging = True
        new_value = change['new']
        new_value = self._restrict_value(new_value)
        quib_type = self.quib.get_type()
        if np.issubdtype(quib_type, np.integer):
            new_value = round(new_value)
        new_value = self.quib.get_type()(new_value)
        self._inverse_assign(value=new_value)

        # call mouse drop using denounce timer
        if self._is_dragging:
            self.denounce_timer.call(change)

    def _get_attr(self, attr):
        try:
            return getattr(self.widget, attr)
        except AttributeError:
            return None

    def _get_min_max_step(self):
        return self._get_attr('min'), self._get_attr('max'), self._get_attr('step')

    def _validate_value(self, value):
        value_arr = np.array(value)
        mn, mx, step = self._get_min_max_step()
        if mn is not None and np.any(value_arr < mn):
            raise ValueError(f"Value {value} is less than minimum value {mn}")
        if mx is not None and np.any(value_arr > mx):
            raise ValueError(f"Value {value} is greater than maximum value {mx}")
        if step is not None and mn is not None:
            r = (value_arr - mn) / step
            if not np.all(np.isclose(r, np.round(r), atol=1e-8)):
                raise ValueError(f"Value {value} is not a multiple of step {step}")

    def _restrict_value(self, value):
        mn, mx, step = self._get_min_max_step()
        if mn is not None:
            value = np.maximum(value, mn)
        if mx is not None:
            value = np.minimum(value, mx)
        if step is not None and step != 0 and mn is not None:
            value = mn + np.round((value - mn) / step) * step
        return value

    def _on_quib_change(self, value):
        self._validate_value(value)
        with self.within_quib_set_context():
            QuibyWidgetTrait.original_set(self.trait, self.widget, value)

    def on_mouse_drop(self, change):
        self._is_dragging = False
        end_dragging(id(self))

    def set_widget_to_update_quib_upon_change(self):
        self.widget.observe(self._on_widget_change, self.trait.name)

    def set_quib_to_update_widget_upon_change(self):
        self.quib.add_callback(self._on_quib_change)

    def _inverse_assign(self, value: Any, on_drag: bool = False):
        assignment = create_assignment(value, path=[], tolerance=self.get_tolerance(value))
        get_override_group_for_quib_changes([AssignmentToQuib(self.quib, assignment)]).apply()

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
