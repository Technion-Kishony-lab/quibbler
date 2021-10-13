"""
Override 3rd party library functions to return quibs (each function and its respective quib type)
when called with quib arguments.
"""
import numpy as np
from functools import wraps
from typing import Type, Any, Callable, Optional, List, Tuple, Set
from matplotlib import widgets
from matplotlib.axes import Axes

from pyquibbler.quib import ImpureFunctionQuib, DefaultFunctionQuib, FunctionQuib, GraphicsFunctionQuib
from pyquibbler.quib.function_quibs.elementwise_quib import ElementWiseQuib
from pyquibbler.quib.function_quibs.transpositional_quib import TranspositionalQuib
from pyquibbler.quib.graphics import global_collecting
from pyquibbler.quib.graphics.elements.slider_graphics_function_quib import SliderGraphicsFunctionQuib
from pyquibbler.quib.graphics.elements.checkbuttons_graphics_function_quib import CheckButtonsGraphicsFunctionQuib
from pyquibbler.quib.graphics.elements.radiobuttons_graphics_function_quib import RadioButtonsGraphicsFunctionQuib
from pyquibbler.quib.graphics.replacing_graphics_function_quib import ReplacingGraphicsFunctionQuib
from pyquibbler.utils import ensure_only_run_once_globally

'''
Functions that should not be overridden as they cause certain issue:
np.maximum, np.minimum
__eq__  
'''

NUMPY_OVERRIDES = [
    (np, [
        (DefaultFunctionQuib, {"abs", "average", "max", "min", "arange", "polyfit",
                               "linspace", "polyval", "array", "genfromtxt", 'prod'}),
        (GraphicsFunctionQuib, {'apply_along_axis', 'apply_over_axes'}),
        (TranspositionalQuib, {'reshape', 'rot90', 'ravel', 'concatenate', 'repeat', 'full', 'concatenate',
                               }),
        (ElementWiseQuib, {'add', 'square',  "sin", "cos", "tan", "sinh", "cosh", "tanh", "real", "imag",
                           "arcsin", "arccos", "arctan", "arcsinh", "arccosh", "arctanh",
                           "exp", "exp2", "expm1",
                           "log", "log2", "log1p", "log10",
                           "sqrt", "int", "float", "ceil", "floor", "round", 'around'
                           })
    ]),
    (np.random, [
        (ImpureFunctionQuib, {'rand', 'randn', 'randint'})
    ])
]

MPL_OVERRIDES = [
    (Axes, [
        (GraphicsFunctionQuib, {'plot', 'imshow', 'text', 'bar', 'hist', 'pie', 'legend'})
    ]),
    (Axes, [
        (ReplacingGraphicsFunctionQuib, {'set_xlim', 'set_ylim', 'set_title', 'set_xlabel', 'set_ylabel', 'set_visible', 'set_facecolor'})
    ]),
    (widgets, [
        (SliderGraphicsFunctionQuib, {'Slider'}),
        (CheckButtonsGraphicsFunctionQuib, {'CheckButtons'}),
        (RadioButtonsGraphicsFunctionQuib, {'RadioButtons'})
    ])
]


def wrap_overridden_graphics_function(func: Callable) -> Callable:
    @wraps(func)
    def _wrapper(*args, **kwargs):
        # We need overridden funcs to be run in `overridden_graphics_function` context manager
        # so artists will be collected
        with global_collecting.overridden_graphics_function():
            return func(*args, **kwargs)

    return _wrapper


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


def apply_overrides(override_list: List[Tuple[Any, List[Tuple[Type[FunctionQuib], Set[str]]]]],
                    function_wrapper: Optional[Callable[[Callable], Callable]] = None):
    for obj, overrides_per_quib_type in override_list:
        for quib_type, func_names in overrides_per_quib_type:
            for func_name in func_names:
                override_func(obj, func_name, quib_type, function_wrapper)


@ensure_only_run_once_globally
def override_all():
    """
    Overrides all modules (such as numpy and matplotlib) to support quibs
    """
    apply_overrides(NUMPY_OVERRIDES)
    apply_overrides(MPL_OVERRIDES, wrap_overridden_graphics_function)
