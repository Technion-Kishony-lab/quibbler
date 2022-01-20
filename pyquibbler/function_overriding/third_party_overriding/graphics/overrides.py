import matplotlib.image
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override
from pyquibbler.function_overriding.third_party_overriding.graphics.helpers import axes_override, \
    replacing_axes_override, widget_override
from pyquibbler.quib.func_calling.func_calls import RadioButtonsQuibFuncCall, SliderQuibFuncCall, \
    RectangleSelectorQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.plot_call import PlotQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.checkbuttons_call import CheckButtonsQuibFuncCall


def create_graphics_overrides():
    return [
        axes_override('plot', quib_function_call_cls=PlotQuibFuncCall),

        axes_override('imshow'), axes_override('text'), axes_override('bar'), axes_override('hist'),
        axes_override('pie'), axes_override('legend'), axes_override('_sci'), axes_override('matshow'),
        axes_override('scatter'),

        replacing_axes_override('set_xlim'), replacing_axes_override('set_ylim'),
        replacing_axes_override('set_xticks'), replacing_axes_override('set_yticks'),
        replacing_axes_override('set_xlabel'), replacing_axes_override('set_ylabel'),
        replacing_axes_override('set_title'), replacing_axes_override('set_visible'),
        replacing_axes_override('set_facecolor'),

        widget_override("RadioButtons", quib_function_call_cls=RadioButtonsQuibFuncCall),
        widget_override("Slider", quib_function_call_cls=SliderQuibFuncCall),
        widget_override("CheckButtons", quib_function_call_cls=CheckButtonsQuibFuncCall),
        widget_override("RectangleSelector", quib_function_call_cls=RectangleSelectorQuibFuncCall),

        override(matplotlib.image, func_name='imread', is_file_loading_func=True)
    ]
