# flake8: noqa

import matplotlib.image
from pyquibbler.function_overriding.third_party_overriding.general_helpers import override
from pyquibbler.function_overriding.third_party_overriding.graphics.helpers import axes_override, \
    replacing_axes_override, widget_override
from pyquibbler.quib.func_calling.func_calls import RadioButtonsQuibFuncCall, SliderQuibFuncCall, \
    RectangleSelectorQuibFuncCall,  CheckButtonsQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.plot_call import PlotQuibFuncCall


def create_graphics_overrides():
    return [
        axes_override(
            'plot', quib_function_call_cls=PlotQuibFuncCall),

        *(axes_override(func_name) for func_name in (
            'imshow',
            'text',
            'bar',
            'hist',
            'pie',
            'legend',
            '_sci',
            'matshow',
            'scatter',
        )),

        *(replacing_axes_override(func_name) for func_name in (
            'set_xlim',
            'set_ylim',
            'set_xticks',
            'set_yticks',
            'set_xlabel',
            'set_ylabel',
            'set_title',
            'set_visible',
            'set_facecolor',
        )),

        *(widget_override(func_name, quib_function_call_cls=cls) for func_name, cls in (
            ('RadioButtons',        RadioButtonsQuibFuncCall),
            ('Slider',              SliderQuibFuncCall),
            ('CheckButtons',        CheckButtonsQuibFuncCall),
            ('RectangleSelector',   RectangleSelectorQuibFuncCall),
            # TODO: add TextBox
        )),

        override(matplotlib.image, 'imread', is_file_loading_func=True)
    ]
