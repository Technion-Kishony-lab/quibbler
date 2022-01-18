import matplotlib.widgets

from pyquibbler.function_overriding.third_party_overriding.graphics.graphics_overriding import GraphicsOverride
from pyquibbler.quib.function_calling.func_calls import RadioButtonsRunner, SliderRunner, \
    RectangleSelectorRunner
from pyquibbler.quib.function_calling.func_calls.known_graphics.widgets.checkbuttons_runner import \
    CheckButtonsRunner


def widget_override(func_name, runner):
    from pyquibbler.function_definitions.function_definition import create_function_definition

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
