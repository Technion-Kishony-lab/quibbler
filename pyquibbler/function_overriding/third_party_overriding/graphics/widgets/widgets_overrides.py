import matplotlib.widgets

from pyquibbler.function_overriding.third_party_overriding.graphics.graphics_overriding import GraphicsOverride
from pyquibbler.quib.func_calling.func_calls import RadioButtonsQuibFuncCall, SliderQuibFuncCall, \
    RectangleSelectorQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.checkbuttons_call import \
    CheckButtonsQuibFuncCall


def widget_override(func_name, runner):
    from pyquibbler.function_definitions.func_definition import create_func_definition

    return GraphicsOverride(func_name, module_or_cls=matplotlib.widgets, function_definition=create_func_definition(
                                        quib_function_call_cls=runner
                                    )
                                    )


def create_widget_overrides():
    return [
        widget_override("RadioButtons", RadioButtonsQuibFuncCall),
        widget_override("Slider", SliderQuibFuncCall),
        widget_override("CheckButtons", CheckButtonsQuibFuncCall),
        widget_override("RectangleSelector", RectangleSelectorQuibFuncCall),
    ]
