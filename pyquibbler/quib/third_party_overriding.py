import numpy as np
import functools
from typing import Type

from pyquibbler.quib import DefaultFunctionQuib, HolisticFunctionQuib, FunctionQuib
from pyquibbler.quib.utils import is_there_a_quib_in_args
from pyquibbler.utils import ensure_only_run_once_globally


def override_numpy_function(quib_type: Type[FunctionQuib], func_name: str):
    original_function = getattr(np, func_name)

    @functools.wraps(original_function)
    def _wrapper(*args, **kwargs):
        if is_there_a_quib_in_args(args, kwargs):
            return quib_type.create(func=original_function, func_args=args, func_kwargs=kwargs)
        return original_function(*args, **kwargs)

    setattr(np, func_name, _wrapper)


@ensure_only_run_once_globally
def override_numpy_functions():
    """
    Override numpy functions to return quibs (each function and her respective quib type) instead of running
    the function if ANY of the arguments are quibs.
    If no arguments are quibs, simply run the function
    """
    quib_types_with_function_names_to_override = [
        (DefaultFunctionQuib, [
            "abs", "average", "around", "square", "repeat"
        ]),
        (
            HolisticFunctionQuib, [
                'apply_along_axis', 'apply_over_axes', 'vectorize']
        )
    ]

    for quib_type, function_names in quib_types_with_function_names_to_override:
        for function_name in function_names:
            override_numpy_function(quib_type, function_name)

