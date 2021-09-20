import functools
from typing import Callable

import numpy as np
from matplotlib import pyplot as plt

from pyquibbler.graphics import global_collecting
from pyquibbler.graphics.artists_redrawer import ArtistsRedrawer
from pyquibbler.quib.utils import iter_quibs_in_args, call_func_with_quib_values


def override_axes_method(method_name: str):
    """
    Override an axes method to create a method that will add an artistsredrawer to any quibs in the arguments

    :param method_name - name of axes method
    """
    cls = plt.Axes
    original_method = getattr(cls, method_name)

    def override(*args, **kwargs):
        artists = call_func_with_quib_values(func=original_method, args=args, kwargs=kwargs)
        if global_collecting.COLLECTING_GLOBAL_ARTISTS:
            global_collecting.GRAPHICS_CALLS_COLLECTED.append(
                global_collecting.GraphicsFunctionCall(original_method, args, kwargs)
            )
            global_collecting.ARTISTS_COLLECTED.extend(artists)
        else:
            redrawer = ArtistsRedrawer(
                artists=artists,
                func=original_method,
                args=args,
                kwargs=kwargs
            )
            for quib in iter_quibs_in_args(args, kwargs):
                quib.add_artists_redrawer(redrawer)

        return artists

    setattr(cls, method_name, override)


OVERRIDDEN_AXES_METHODS = ['plot', 'imshow', 'text']
OVERRIDDEN_APPLY_FUNCTIONS = ['apply_along_axis', 'apply_over_axes', 'vectorize']


def override_apply_func(module, func_name):
    original_method = getattr(module, func_name)

    def apply(*args, **kwargs):
        from pyquibbler.quib.holistic_function_quib import HolisticFunctionQuib
        return HolisticFunctionQuib.create(
            func_args=args,
            func_kwargs=kwargs,
            func=original_method,
        )

    setattr(module, func_name, apply)


def run_once_globally(func: Callable):
    did_run = False

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        nonlocal did_run
        if not did_run:
            func(*args, **kwargs)
            did_run = True

    return _wrapper


@run_once_globally
def override_applier_functions():
    """
    Override all applier functions so we can create HolisticFunctionQuibs when they are ran
    """
    for apply_method in OVERRIDDEN_APPLY_FUNCTIONS:
        override_apply_func(np, apply_method)


@run_once_globally
def override_axes_methods():
    """
    Override all axes methods so we can add redrawers to the relevant quibs
    """
    for axes_method in OVERRIDDEN_AXES_METHODS:
        override_axes_method(axes_method)


