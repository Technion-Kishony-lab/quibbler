"""
Override 3rd party library functions to return quibs (each function and its respective quib type)
when called with quib arguments.
"""
import matplotlib
import matplotlib.image
import numpy as np
from functools import wraps
from typing import Type, Any, Callable, Optional, List, Tuple, Set
from matplotlib import widgets
from matplotlib.axes import Axes
import matplotlib.pyplot as plt

from pyquibbler.quib import ImpureFunctionQuib, DefaultFunctionQuib, FunctionQuib, GraphicsFunctionQuib
from pyquibbler.quib.function_quibs.elementwise_function_quib import ElementWiseFunctionQuib
from pyquibbler.quib.function_quibs.transpositional import TranspositionalFunctionQuib, ConcatenateFunctionQuib
from pyquibbler.quib.graphics import global_collecting, ReductionAxisWiseGraphicsFunctionQuib, \
    ApplyAlongAxisGraphicsFunctionQuib
from pyquibbler.quib.graphics import QVectorize
from pyquibbler.quib.graphics.axiswise_function_quibs.axiswise_function_quib import \
    AccumulationAxisWiseGraphicsFunctionQuib
from pyquibbler.quib.graphics.plot_graphics_function_quib import PlotGraphicsFunctionQuib
from pyquibbler.quib.graphics.widgets import SliderGraphicsFunctionQuib, CheckButtonsGraphicsFunctionQuib, \
    RadioButtonsGraphicsFunctionQuib, RectangleSelectorGraphicsFunctionQuib, QRadioButtons, QRectangleSelector, \
    TextBoxGraphicsFunctionQuib
from pyquibbler.quib.graphics.replacing_graphics_function_quib import ReplacingGraphicsFunctionQuib
from pyquibbler.quib.graphics.widgets.slider import QSlider
from pyquibbler.utils import ensure_only_run_once_globally

'''
Functions that should not be overridden as they cause certain issue:
np.maximum, np.minimum
__eq__
'''


def wrap_overridden_graphics_function(func: Callable) -> Callable:
    @wraps(func)
    def _wrapper(*args, **kwargs):
        # We need overridden funcs to be run in `overridden_graphics_function` context manager
        # so artists will be collected
        with global_collecting.overridden_graphics_function():
            return func(*args, **kwargs)

    return _wrapper


NON_QUIB_OVERRIDES = [
    (widgets, {
        'RectangleSelector': wrap_overridden_graphics_function(QRectangleSelector),
        'RadioButtons': wrap_overridden_graphics_function(QRadioButtons),
        'Slider': wrap_overridden_graphics_function(QSlider),
    }),
    (np, {
        'vectorize': QVectorize
    })
]

NUMPY_OVERRIDES = [
    (np, [
        (DefaultFunctionQuib, {
            'arange', 'polyfit', 'interp',
            'linspace', 'polyval', 'genfromtxt', 'corrcoef',
        }),
        (GraphicsFunctionQuib, {'apply_over_axes'}),
        (TranspositionalFunctionQuib, {
            'reshape', 'rot90', 'ravel', 'repeat', 'full',
            'squeeze', 'array', 'swapaxes', 'expand_dims', 'tile', 'transpose', 'asarray'
        }),
        (ConcatenateFunctionQuib, {'concatenate'}),
        (ElementWiseFunctionQuib, {
            'sin', 'cos', 'tan',                                # trigonometric
            'arcsin', 'arccos', 'arctan',                       # inverse-trigonometric
            'sinh', 'cosh', 'tanh',                             # hyperbolic
            'arcsinh', 'arccosh', 'arctanh',                    # inverse-hyperbolic
            'hypot', 'arctan2',                                 # trigonometric 2-arguments
            'degrees', 'radians', 'deg2rad', 'rad2deg',         # angles
            'real', 'imag', 'abs', 'absolute', 'angle',         # complex numbers
            'conj', 'conjugate',                                #
            'exp', 'exp2', 'expm1',                             # exponentials
            'log', 'log2', 'log1p', 'log10',                    # logs
            'add', 'subtract', 'multiply', 'divide', 'power',   # two-element arithmetics
            'true_divide', 'floor_divide', 'float_power',       #
            'fmod', 'mod', 'remainder', 'divmod',               #
            'reciprocal', 'positive', 'negative', 'modf',       # one-element arithmetics
            'ceil', 'floor', 'round', 'around', 'rint',         # rounding
            'fix', 'trunc',                                     #
            'square', 'sqrt',                                   # square, sqrt
            'fmax', 'fmin',                                     # min/max
            'lcm', 'gcd',                                       # rational
            'int', 'float',                                     # casting
            'i0', 'sinc', 'sign'                                # other
        }),
        (ApplyAlongAxisGraphicsFunctionQuib, {'apply_along_axis'}),
        (ReductionAxisWiseGraphicsFunctionQuib, {
            'min', 'amin', 'max', 'amax',                       # min/max
            'argmin', 'argmax', 'nanargmin', 'nanargmax',       # arg-min/max
            'sum', 'prod', 'nanprod', 'nansum',                 # sum/prod
            'any', 'all',                                       # logical
            'average', 'mean', 'var', 'std', 'median',          # statistics
            'diff', 'sort',                                     # other
        }),
        (AccumulationAxisWiseGraphicsFunctionQuib, {
            'cumsum', 'cumprod', 'cumproduct', 'nancumsum', 'nancumprod'
        }),
    ]),
    (np.random, [
        (ImpureFunctionQuib, {'rand', 'randn', 'randint'})
    ]),
    (np.linalg, [
        (ReductionAxisWiseGraphicsFunctionQuib, {'norm'})
    ])
]

MPL_OVERRIDES = [
    (Axes, [
        (GraphicsFunctionQuib, {'imshow', 'text', 'bar', 'hist', 'pie', 'legend', '_sci', 'matshow', 'scatter'}),
        (PlotGraphicsFunctionQuib, {'plot'}),
    ]),
    (plt, [
        (DefaultFunctionQuib, {'imread'})
    ]),
    (Axes, [
        (ReplacingGraphicsFunctionQuib, {'set_xlim', 'set_ylim',
                                         'set_xticks', 'set_yticks',
                                         'set_xlabel', 'set_ylabel',
                                         'set_title', 'set_visible', 'set_facecolor'})
    ]),
    (widgets, [
        (SliderGraphicsFunctionQuib, {'Slider'}),
        (TextBoxGraphicsFunctionQuib, {'TextBox'}),
        (CheckButtonsGraphicsFunctionQuib, {'CheckButtons'}),
        (RadioButtonsGraphicsFunctionQuib, {'RadioButtons'}),
        (RectangleSelectorGraphicsFunctionQuib, {'RectangleSelector'})
    ]),
    (matplotlib.image, [
        (ImpureFunctionQuib, {'imread'})
    ])
]


def override_func(obj: Any, name: str, quib_type: Type[FunctionQuib],
                  function_wrapper: Optional[Callable[[Callable], Callable]] = None):
    """
    Replace obj.name with a wrapper function that returns a quib of type quib_type.
    If function_wrapper is given, wrap the original function with it before passing it to the function quib wrapper.
    """
    func = getattr(obj, name)
    if function_wrapper is not None:
        func = function_wrapper(func)
    func = quib_type.create_wrapper(func)
    setattr(obj, name, func)


def apply_quib_creating_overrides(override_list: List[Tuple[Any, List[Tuple[Type[FunctionQuib], Set[str]]]]],
                                  function_wrapper: Optional[Callable[[Callable], Callable]] = None):
    for obj, overrides_per_quib_type in override_list:
        for quib_type, func_names in overrides_per_quib_type:
            for func_name in func_names:
                override_func(obj, func_name, quib_type, function_wrapper)


def apply_non_quib_overrides():
    for module, overrides in NON_QUIB_OVERRIDES:
        for name, replacement in overrides.items():
            overridden = getattr(module, name)
            setattr(module, name, replacement)
            replacement.__overridden__ = overridden


@ensure_only_run_once_globally
def override_all():
    """
    Overrides all modules (such as numpy and matplotlib) to support quibs
    """
    apply_non_quib_overrides()
    apply_quib_creating_overrides(NUMPY_OVERRIDES)
    apply_quib_creating_overrides(MPL_OVERRIDES, wrap_overridden_graphics_function)
