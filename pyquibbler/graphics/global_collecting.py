import contextlib
from collections import Callable
from dataclasses import dataclass
from typing import Tuple, Mapping

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
    """
    A context manager to begin global collecting of artists and graphics calls- during this time, no artist redawers
    will be created. Instead, a list of artists will be created as well as a list of all the graphics calls that
    occurred
    """
    start_global_graphics_collecting_mode()
    yield
    end_global_graphics_collecting_mode()
