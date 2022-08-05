# flake8: noqa

import matplotlib.image
from matplotlib.axes import Axes

from pyquibbler.function_overriding.third_party_overriding.general_helpers import file_loading_override, \
    override_not_implemented
from pyquibbler.function_overriding.third_party_overriding.graphics.helpers import axes_override, \
    axes_setter_override, widget_override, axes_lim_override, plot_override, patches_override
from pyquibbler.quib.func_calling.func_calls import RadioButtonsQuibFuncCall, SliderQuibFuncCall, \
    RectangleSelectorQuibFuncCall,  CheckButtonsQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.plot_call import PlotQuibFuncCall
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.textbox_call import TextBoxQuibFuncCall


def create_graphics_overrides():
    return [
        plot_override(
            'plot', quib_function_call_cls=PlotQuibFuncCall),

        plot_override(
            'scatter'),

        *(patches_override(func_name) for func_name in (
            'Arc',
            'Arrow',
            'ArrowStyle',
            'BoxStyle',
            'Circle',
            'CirclePolygon',
            'ConnectionPatch',
            'ConnectionStyle',
            'Ellipse',
            'FancyArrow',
            'FancyArrowPatch',
            'FancyBboxPatch',
            'Patch',
            'RegularPolygon',
        )),

        *(axes_override(func_name) for func_name in (

            # Obtained by: set(dir(Axes)) & set(dir(plt)), then commented out manually:

            'acorr',
            'angle_spectrum',
            'annotate',
            'arrow',
            # 'autoscale',
            # 'axes',  # Overloaded as not implemented
            'axhline',
            'axhspan',
            # 'axis',
            'axline',
            'axvline',
            'axvspan',
            'bar',
            # 'bar_label',  # Overloaded as not implemented
            'barbs',
            'barh',
            'boxplot',
            'broken_barh',
            # 'cla',
            # 'clabel',
            'cohere',
            'contour',
            'contourf',
            'csd',
            # 'draw',
            'errorbar',
            'eventplot',
            'fill',
            'fill_between',
            'fill_betweenx',
            # 'findobj',
            # 'grid',  # Overloaded as not implemented
            'hexbin',
            'hist',
            'hist2d',
            'hlines',
            'imshow',
            'legend',
            # 'locator_params',
            'loglog',
            'magnitude_spectrum',
            # 'margins',
            'matshow',
            # 'minorticks_off',
            # 'minorticks_on',
            'pcolor',
            'pcolormesh',
            'phase_spectrum',
            'pie',
            # 'plot',  # implemented as plot_override
            'plot_date',
            'psd',
            'quiver',
            # 'quiverkey',
            # 'scatter'  # implemented as plot_override
            'semilogx',
            'semilogy',
            'specgram',
            'spy',
            'stackplot',
            'stairs',
            'stem',
            'step',
            'streamplot',
            'table',
            'text',
            # 'tick_params',
            # 'ticklabel_format',
            'tricontour',
            'tricontourf',
            'tripcolor',
            'triplot',
            # 'twinx',
            # 'twiny',
            'violinplot',
            'vlines',
            'xcorr',
        )),

        *(axes_setter_override(func_name) for func_name in (
            # Obtained by: [func for func in dir(Axes) if func.startswith('set')], then commented out manually:

            #'set',
            #'set_adjustable',
            #'set_agg_filter',
            'set_alpha',
            #'set_anchor',
            #'set_animated',
            'set_aspect',
            #'set_autoscale_on',
            #'set_autoscalex_on',
            #'set_autoscaley_on',
            #'set_axes_locator',
            #'set_axis_off',
            #'set_axis_on',
            #'set_axisbelow',
            #'set_box_aspect',
            #'set_clip_box',
            #'set_clip_on',
            #'set_clip_path',
            #'set_contains',
            'set_facecolor',
            'set_fc',
            #'set_figure',
            #'set_frame_on',
            #'set_gid',
            #'set_in_layout',
            #'set_label',
            #'set_navigate',
            #'set_navigate_mode',
            #'set_path_effects',
            #'set_picker',
            'set_position',
            #'set_prop_cycle',
            #'set_rasterization_zorder',
            #'set_rasterized',
            #'set_sketch_params',
            #'set_snap',
            'set_title',
            #'set_transform',
            #'set_url',
            'set_visible',
            #'set_xbound',
            'set_xlabel',
            #'set_xlim',  # implemented as axes_lim_override
            #'set_xmargin',
            'set_xscale',
            'set_xticklabels',
            'set_xticks',
            #'set_ybound',
            'set_ylabel',
            #'set_ylim',  # implemented as axes_lim_override
            #'set_ymargin',
            'set_yscale',
            'set_yticklabels',
            'set_yticks',
            #'set_zorder'
        )),

        *(override_not_implemented(module_or_cls=Axes,
                                   func_name=func_name,
                                   message=message) for func_name, message in (
            ('axis', 'Use plt.xlim, plt.ylim, or ax.set_xlim, ax.set_ylim instead.'),
            ('grid', ''),
            ('bar_label', 'Set the labels in the bar creation method'),
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
