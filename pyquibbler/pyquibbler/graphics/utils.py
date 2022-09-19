from collections import defaultdict
from typing import List, Dict, Iterable
from contextlib import contextmanager

from matplotlib.axes import Axes
from matplotlib.artist import Artist

from .global_collecting import ArtistsCollector, AxesWidgetsCollector, AxesCreationPreventor


def get_axeses_to_artists(artists: Iterable[Artist]) -> Dict[Axes, List[Artist]]:
    """
    Map axes -> artists
    """
    axeses_to_artists = defaultdict(list)
    for artist in artists:
        axeses_to_artists[artist.axes].append(artist)
    return axeses_to_artists


def remove_artist(artist: Artist):
    """
    Remove an artist from its axes (does NOT redraw)
    """
    from pyquibbler.quib.graphics import artist_wrapper
    artist_wrapper.clear_all_quibs(artist)
    if artist.axes:

        ax = artist.axes
        artist_array = ax._children

        try:
            artist.remove()
            artist.axes = ax
        except NotImplementedError:
            pass

        try:
            artist_array.remove(artist)
        except ValueError:
            pass  # artists not in artist array have been observed in the wild


def remove_artists(artists: Iterable[Artist]):
    for artist in artists:
        remove_artist(artist)


def get_axeses_to_starting_indices(artists: List[Artist]) -> Dict[Axes, int]:
    """
    Map axes -> starting_index
    """
    axeses_to_indices = {}
    for axes, artists in get_axeses_to_artists(artists).items():
        array = axes._children
        # Get the index of the artist that appears first in the array
        index = next(i for i, artist in enumerate(array) if artist in artists)
        axeses_to_indices[axes] = index

    return axeses_to_indices


@contextmanager
def remove_created_graphics():
    with ArtistsCollector() as collector, \
            AxesWidgetsCollector() as widgets_collector, \
            AxesCreationPreventor():
        yield

    remove_artists(collector.objects_collected)

    for widget in widgets_collector.objects_collected:
        widget.set_active(False)
        widget.set_visible(False)
