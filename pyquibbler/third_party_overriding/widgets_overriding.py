import functools

import matplotlib.widgets
from typing import Callable

from pyquibbler.graphics import global_collecting
from pyquibbler.quib.function_quibs.utils import ArgsValues
from pyquibbler.quib.refactor.graphics.widgets.q_radio_buttons import QRadioButtons
from pyquibbler.third_party_overriding.definitions import OverrideDefinition
from pyquibbler.third_party_overriding.graphics_overriding import GraphicsOverrideDefinition


def wrap_overridden_graphics_function(func: Callable) -> Callable:
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        # We need overridden funcs to be run in `overridden_graphics_function` context manager
        # so artists will be collected
        with global_collecting.overridden_graphics_function():
            return func(*args, **kwargs)

    return _wrapper


widget_class_names_to_quib_supporting_widget = {
    'RadioButtons': wrap_overridden_graphics_function(QRadioButtons)
}


def on_change(args_values, new_value):
    from pyquibbler.quib.refactor.quib import Quib
    active = args_values.get('active')
    if isinstance(active, Quib):
        active.assign_value(args_values.get('labels').index(new_value))


class WidgetOverrideDefinition(GraphicsOverrideDefinition):

    def _run_previous_func(self, previous_func: Callable, args_values, *args, **kwargs):
        res = previous_func(*args, **kwargs)
        res.on_clicked(functools.partial(on_change, args_values))
        return res


WidgetOverrideDefinition = functools.partial(WidgetOverrideDefinition, module_or_cls=matplotlib.widgets)


def switch_widgets_to_quib_supporting_widgets():
    for widget_class_name, quib_supporting_widget in widget_class_names_to_quib_supporting_widget.items():
        setattr(matplotlib.widgets, widget_class_name, quib_supporting_widget)


widgets = [
    WidgetOverrideDefinition(
        func_name="RadioButtons"
    )
]


def override_widgets_with_quib_creators():
    for widget_definition in widgets:
        widget_definition.override()
