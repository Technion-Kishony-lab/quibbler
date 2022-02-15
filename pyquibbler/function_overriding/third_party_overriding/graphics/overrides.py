# flake8: noqa

import matplotlib.image
from pyquibbler.function_overriding.third_party_overriding.general_helpers import file_loading_override
from pyquibbler.function_overriding.third_party_overriding.graphics.helpers import axes_override, \
    replacing_axes_override, widget_override, axes_lim_override
from pyquibbler.quib.func_calling.func_calls import RadioButtonsQuibFuncCall, SliderQuibFuncCall, \
    RectangleSelectorQuibFuncCall,  CheckButtonsQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.plot_call import PlotQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.textbox_call import TextBoxQuibFuncCall


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
            'set_xticks',
            'set_yticks',
            'set_xticklabels',
            'set_yticklabels',
            'set_xlabel',
            'set_ylabel',
            'set_title',
            'set_visible',
            'set_facecolor',
        )),

        *(axes_lim_override(func_name) for func_name in (
            'set_xlim',
            'set_ylim',
        )),

        *(widget_override(func_name, quib_function_call_cls=cls) for func_name, cls in (
            ('RadioButtons',        RadioButtonsQuibFuncCall),
            ('Slider',              SliderQuibFuncCall),
            ('CheckButtons',        CheckButtonsQuibFuncCall),
            ('RectangleSelector',   RectangleSelectorQuibFuncCall),
            ('TextBox',             TextBoxQuibFuncCall),
        )),

        file_loading_override(matplotlib.image, 'imread')
    ]
