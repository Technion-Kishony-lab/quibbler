import functools

from typing import Callable

import matplotlib.widgets

from pyquibbler.graphics import global_collecting
from pyquibbler.quib.graphics.widgets import QRadioButtons


def wrap_overridden_graphics_function(func: Callable) -> Callable:
    # TODO: add docs
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        # We need overridden funcs to be run in `overridden_graphics_function` context manager
        # so artists will be collected
        with global_collecting.overridden_graphics_function():
            return func(*args, **kwargs)

    return _wrapper


widget_class_names_to_quib_supporting_widget = {
    'RadioButtons': wrap_overridden_graphics_function(QRadioButtons),
    'CheckBox': None
}


def switch_widgets_to_quib_supporting_widgets():
    for widget_class_name, quib_supporting_widget in widget_class_names_to_quib_supporting_widget.items():
        setattr(matplotlib.widgets, widget_class_name, quib_supporting_widget)
