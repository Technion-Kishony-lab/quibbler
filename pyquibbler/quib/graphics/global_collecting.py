import contextlib
import functools
import threading

from matplotlib.artist import Artist

CURRENT_THREAD_ID = None
COLLECTING_GLOBAL_ARTISTS = False
IN_OVERRIDEN_FUNCTION = False
ARTISTS_COLLECTED = []


def start_global_graphics_collecting_mode():
    global CURRENT_THREAD_ID
    global ARTISTS_COLLECTED
    global COLLECTING_GLOBAL_ARTISTS

    CURRENT_THREAD_ID = threading.get_ident()
    ARTISTS_COLLECTED = []
    COLLECTING_GLOBAL_ARTISTS = True


def get_artists_collected():
    return list(set(ARTISTS_COLLECTED))


def end_global_graphics_collecting_mode():
    global COLLECTING_GLOBAL_ARTISTS
    COLLECTING_GLOBAL_ARTISTS = False


@contextlib.contextmanager
def global_graphics_collecting_mode():
    """
    A context manager to begin global collecting of artists.
    After exiting the context manager use `get_artists_collected` to get a list of artists created during this time
    """
    def wrap_artist_creation(func):
        @functools.wraps(func)
        def wrapped_init(self, *args, **kwargs):
            res = func(self, *args, **kwargs)
            if threading.get_ident() == CURRENT_THREAD_ID and IN_OVERRIDEN_FUNCTION:
                ARTISTS_COLLECTED.append(self)
            return res
        return wrapped_init

    old_init = Artist.__init__
    Artist.__init__ = wrap_artist_creation(Artist.__init__)
    start_global_graphics_collecting_mode()
    yield
    end_global_graphics_collecting_mode()
    Artist.__init__ = old_init


@contextlib.contextmanager
def overriden_graphics_function():
    global IN_OVERRIDEN_FUNCTION
    IN_OVERRIDEN_FUNCTION = True
    yield
    IN_OVERRIDEN_FUNCTION = False