import functools
from dataclasses import dataclass

import matplotlib.widgets
from typing import Callable

from pyquibbler.third_party_overriding.graphics.graphics_overriding import GraphicsOverrideDefinition


def on_change_radio_buttons(args_values, new_value):
    from pyquibbler.quib.refactor.quib import Quib
    active = args_values.get('active')
    if isinstance(active, Quib):
        active.assign_value(args_values.get('labels').index(new_value))


def on_change_slider(args_values, new_value):
    from pyquibbler.quib.refactor.quib import Quib
    val = args_values.get('valinit')
    if isinstance(val, Quib):
        val.assign_value(new_value)


def set_change_slider(res, callback):
    res.on_changed(callback)
    res.on_release = callback


@dataclass
class WidgetOverrideDefinition(GraphicsOverrideDefinition):

    on_change: Callable = None
    set_on_change: Callable = None

    def _run_previous_func(self, previous_func: Callable, args_values, *args, **kwargs):
        res = previous_func(*args, **kwargs)
        if self.on_change and self.set_on_change:
            self.set_on_change(res, functools.partial(self.on_change, args_values))
        return res


WidgetOverrideDefinition = functools.partial(WidgetOverrideDefinition, module_or_cls=matplotlib.widgets)

widgets = [
    WidgetOverrideDefinition(
        func_name="RadioButtons",
        on_change=on_change_radio_buttons,
        set_on_change=lambda res, callback: res.on_clicked(callback)
    ),
    WidgetOverrideDefinition(
        func_name="Slider",
        on_change=on_change_slider,
        set_on_change=set_change_slider
    )
]


def override_widgets_with_quib_creators():
    for widget_definition in widgets:
        widget_definition.override()
