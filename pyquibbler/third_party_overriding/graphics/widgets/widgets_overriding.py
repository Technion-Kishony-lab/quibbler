import functools
from dataclasses import dataclass

import matplotlib.widgets
from typing import Callable

from pyquibbler.graphics import global_collecting
from pyquibbler.quib import PathComponent
from pyquibbler.quib.refactor.quib import Quib
from pyquibbler.third_party_overriding.graphics.graphics_overriding import GraphicsOverrideDefinition


def on_change_radio_buttons(widget, args_values, new_value):
    from pyquibbler.quib.refactor.quib import Quib
    active = args_values.get('active')
    if isinstance(active, Quib):
        active.assign_value(args_values.get('labels').index(new_value))


def on_change_slider(widget, args_values, new_value):
    from pyquibbler.quib.refactor.quib import Quib
    val = args_values.get('valinit')
    if isinstance(val, Quib):
        val.assign_value(new_value)


def on_change_checkbuttons(widget, args_values, new_value):
    from pyquibbler import Assignment
    actives = args_values.get('actives')
    if isinstance(actives, Quib):
        buttons_checked = widget.get_status()
        labels = args_values.get('labels')
        new_value_index = labels.index(new_value)
        actives.assign(Assignment(value=buttons_checked[new_value_index],
                                  path=[PathComponent(indexed_cls=list, component=new_value_index)]))


def set_change_slider(res, callback):
    res.on_changed(callback)
    res.on_release = callback


@dataclass
class WidgetOverrideDefinition(GraphicsOverrideDefinition):

    on_change: Callable = None
    set_on_change: Callable = None

    def _run_previous_func(self, previous_func: Callable, args_values, *args, **kwargs):
        with global_collecting.overridden_graphics_function():
            widget = previous_func(*args, **kwargs)
            if self.on_change and self.set_on_change:
                self.set_on_change(widget, functools.partial(self.on_change, widget, args_values))
            return widget


WidgetOverrideDefinition = functools.partial(WidgetOverrideDefinition, module_or_cls=matplotlib.widgets)

WIDGET_DEFINITIONS = [
    WidgetOverrideDefinition(
        func_name="RadioButtons",
        on_change=on_change_radio_buttons,
        set_on_change=lambda res, callback: res.on_clicked(callback)
    ),
    WidgetOverrideDefinition(
        func_name="Slider",
        on_change=on_change_slider,
        set_on_change=set_change_slider
    ),
    WidgetOverrideDefinition(
        func_name="CheckButtons",
        on_change=on_change_checkbuttons,
        set_on_change=lambda res, callback: res.on_clicked(callback)
    )
]

