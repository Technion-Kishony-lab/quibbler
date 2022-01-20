import functools

import matplotlib.widgets
from typing import Callable

from pyquibbler.function_overriding.third_party_overriding.graphics.helpers import GraphicsOverride
from pyquibbler.function_overriding.third_party_overriding.graphics.overrides import create_graphics_overrides
from pyquibbler.graphics import global_collecting
from pyquibbler.graphics.widgets import QRadioButtons, QSlider, QRectangleSelector

widget_class_names_to_quib_supporting_widget = {
    'RadioButtons': QRadioButtons,
    'Slider': QSlider,
    'RectangleSelector': QRectangleSelector
}


def switch_widgets_to_quib_supporting_widgets():
    for widget_class_name, quib_supporting_widget in widget_class_names_to_quib_supporting_widget.items():
        setattr(matplotlib.widgets, widget_class_name, quib_supporting_widget)


def wrap_overridden_graphics_function(func: Callable) -> Callable:
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        # We need overridden funcs to be run in `overridden_graphics_function` context manager
        # so artists will be collected
        with global_collecting.overridden_graphics_function():
            return func(*args, **kwargs)

    return _wrapper


def override_graphics_functions_to_be_within_known_func_ctx():
    for override in create_graphics_overrides():
        if isinstance(override, GraphicsOverride):
            setattr(override.module_or_cls, override.func_name,
                    wrap_overridden_graphics_function(override.original_func))
