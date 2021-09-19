import contextlib
import functools
from typing import Callable, Tuple, Dict, Mapping
from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt

from pyquibbler.graphics.artists_redrawer import ArtistsRedrawer
from pyquibbler.quib.utils import iter_quibs_in_args, call_func_with_quib_values

COLLECTING_GLOBAL_ARTISTS = False
GRAPHICS_CALLS_COLLECTED = []
ARTISTS_COLLECTED = []


@dataclass
class GraphicsFunctionCall:
    func: Callable
    args: Tuple
    kwargs: Mapping

    def run(self):
        return self.func(*self.args, **self.kwargs)


def start_global_graphics_collecting_mode():
    global GRAPHICS_CALLS_COLLECTED
    global ARTISTS_COLLECTED
    global COLLECTING_GLOBAL_ARTISTS

    GRAPHICS_CALLS_COLLECTED = []
    ARTISTS_COLLECTED = []
    COLLECTING_GLOBAL_ARTISTS = True


def get_graphics_calls_collected():
    return GRAPHICS_CALLS_COLLECTED


def get_artists_collected():
    return ARTISTS_COLLECTED


def end_global_graphics_collecting_mode():
    global COLLECTING_GLOBAL_ARTISTS
    COLLECTING_GLOBAL_ARTISTS = False


@contextlib.contextmanager
def global_graphics_collecting_mode():
    start_global_graphics_collecting_mode()
    yield
    end_global_graphics_collecting_mode()


def override_axes_method(method_name: str):
    """
    Override an axes method to create a method that will add an artistsredrawer to any quibs in the arguments

    :param method_name - name of axes method
    """
    cls = plt.Axes
    original_method = getattr(cls, method_name)

    def override(*args, **kwargs):
        artists = call_func_with_quib_values(func=original_method, args=args, kwargs=kwargs)
        if COLLECTING_GLOBAL_ARTISTS:
            GRAPHICS_CALLS_COLLECTED.append(GraphicsFunctionCall(original_method, args, kwargs))
            ARTISTS_COLLECTED.extend(artists)
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


