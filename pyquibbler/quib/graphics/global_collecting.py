import contextlib
import functools
import threading

from matplotlib.artist import Artist

CURRENT_THREAD_ID = None
COLLECTING_GLOBAL_ARTISTS = False
IN_OVERRIDDEN_FUNCTION = False
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
            if threading.get_ident() == CURRENT_THREAD_ID and IN_OVERRIDDEN_FUNCTION:
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
def overridden_graphics_function():
    """
    Any overridden graphics function should be run within this context manager.
    Even in global collecting mode, artists will NOT be collected if not within this context manager.
    This serves as an extra layer of protection to make sure we're only collecting artists from known functions.
    """
    global IN_OVERRIDDEN_FUNCTION
    IN_OVERRIDDEN_FUNCTION = True
    yield
    IN_OVERRIDDEN_FUNCTION = False
