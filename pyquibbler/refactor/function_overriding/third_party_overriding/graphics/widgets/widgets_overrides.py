import functools
from dataclasses import dataclass

import matplotlib.widgets
from typing import Callable

from pyquibbler.refactor.function_overriding.third_party_overriding.graphics.graphics_overriding import GraphicsOverride
from pyquibbler.refactor.quib.function_running.function_runners import RadioButtonsRunner, SliderRunner, \
    RectangleSelectorRunner
from pyquibbler.refactor.quib.function_running.function_runners.known_graphics.widgets.checkbuttons_runner import \
    CheckButtonsRunner


def widget_override(func_name, runner):
    from pyquibbler.refactor.function_definitions.function_definition import create_function_definition

    return GraphicsOverride(func_name, module_or_cls=matplotlib.widgets, function_definition=create_function_definition(
                                        function_runner_cls=runner
                                    )
                                    )


def create_widget_overrides():
    return [
        widget_override("RadioButtons", RadioButtonsRunner),
        widget_override("Slider", SliderRunner),
        widget_override("CheckButtons", CheckButtonsRunner),
        widget_override("RectangleSelector", RectangleSelectorRunner),
    ]
