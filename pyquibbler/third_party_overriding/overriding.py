"""
Override 3rd party library functions to return quibs (each function and its respective quib type)
when called with quib arguments.
"""
import numpy as np
from functools import wraps
from typing import Type, Any, Callable, Optional, List, Tuple
from matplotlib.axes import Axes

from pyquibbler.quib import ImpureFunctionQuib, DefaultFunctionQuib, FunctionQuib, GraphicsFunctionQuib
from pyquibbler.quib.graphics import global_collecting
from pyquibbler.utils import ensure_only_run_once_globally

NUMPY_OVERRIDES = [
    (np, [
        (DefaultFunctionQuib, ["abs", "average", "around", "square", "repeat", "max"]),
        (GraphicsFunctionQuib, ['apply_along_axis', 'apply_over_axes', 'vectorize']),
    ]),
    (np.random, [
        (ImpureFunctionQuib, ['rand', 'randint'])
    ])
]

MPL_OVERRIDES = [
    (Axes, [
        (GraphicsFunctionQuib, ['plot', 'imshow', 'text', 'bar', 'set_xlim', 'set_ylim', 'set_title'])
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


def apply_overrides(override_list: List[Tuple[Any, List[Tuple[Type[FunctionQuib], List[str]]]]],
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
