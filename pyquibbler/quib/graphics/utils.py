from typing import List, Callable, Tuple, Any, Dict, Iterable, Set
from contextlib import contextmanager

from matplotlib.axes import Axes
from matplotlib.artist import Artist
from matplotlib.collections import Collection
from matplotlib.image import AxesImage
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.spines import Spine
from matplotlib.table import Table
from matplotlib.text import Text

from .event_handling import CanvasEventHandler
from .global_collecting import ArtistsCollector

ArrayNameToArtists = Dict[str, List[Artist]]

TYPES_TO_ARTIST_ARRAY_NAMES = {
    Line2D: "lines",
    Collection: "collections",
    Patch: "patches",
    Text: "texts",
    Spine: "spines",
    Table: "tables",
    AxesImage: "images"
}


def get_artist_array_name(artist: Artist):
    return next((
        array_name
        for type_, array_name in TYPES_TO_ARTIST_ARRAY_NAMES.items()
        if isinstance(artist, type_)
    ), "artists")


def get_artist_array(artist: Artist):
    return getattr(artist.axes, get_artist_array_name(artist))


def get_axeses_to_array_names_to_artists(artists: Iterable[Artist]) -> Dict[Axes, ArrayNameToArtists]:
    """
    Creates a mapping of axes -> artist_array_name (e.g. `lines`) -> artists
    """
    axeses_to_array_names_to_artists = {}
    for artist in artists:
        array_names_to_artists = axeses_to_array_names_to_artists.setdefault(artist.axes, {})
        array_names_to_artists.setdefault(get_artist_array_name(artist), []).append(artist)
    return axeses_to_array_names_to_artists


def remove_artist(artist: Artist):
    """
    Remove an artist from its artist array (does NOT redraw)
    """
    get_artist_array(artist).remove(artist)


def get_axeses_to_array_names_to_starting_indices_and_artists(artists: Set[Artist]) \
        -> Dict[Axes, Dict[str, Tuple[int, List[Artist]]]]:
    """
    Creates a mapping of axes -> artists_array_name -> (starting_index, artists)
    """
    axeses_to_array_names_to_indices_and_artists = {}
    for axes, array_names_to_artists in get_axeses_to_array_names_to_artists(artists).items():
        array_names_to_indices_and_artists = {}
        axeses_to_array_names_to_indices_and_artists[axes] = array_names_to_indices_and_artists

        for array_name, array_artists in array_names_to_artists.items():
            exemplifying_artist = array_artists[0]
            array = getattr(exemplifying_artist.axes, array_name)
            array_names_to_indices_and_artists[array_name] = (array.index(exemplifying_artist), array_artists)

    return axeses_to_array_names_to_indices_and_artists


def save_func_and_args_on_artists(artist: Artist, func: Callable, args: Iterable[Any]):
    """
    Set the drawing func and on the artist- this will be used later on when tracking an artist, in order to know how to
    inverse and handle events.
    If there's already a creating func, we assume the lower func that already created the artist is the actual
    drawing func (such as a user func that called plt.plot)
    """
    if getattr(artist, '_quibbler_drawing_func', None) is None:
        artist._quibbler_drawing_func = func
        artist._quibbler_args = args


def track_artist(artist: Artist):
    CanvasEventHandler.get_or_create_initialized_event_handler(artist.figure.canvas)


@contextmanager
def remove_created_artists():
    with ArtistsCollector() as collector:
        yield
    for artist in collector.artists_collected:
        remove_artist(artist)
