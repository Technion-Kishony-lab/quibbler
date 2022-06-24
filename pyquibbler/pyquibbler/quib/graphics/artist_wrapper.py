from typing import Optional, Dict
from matplotlib.artist import Artist

from pyquibbler.quib.quib import Quib

SETTER_QUIBS_NAME = '_quibbler_artist_setter_quibs'
CREATING_QUIB_NAME = '_quibbler_artist_creating_quib'


def get_creating_quib(artist: Artist):
    return getattr(artist, CREATING_QUIB_NAME, None)


def delete_creating_quib_attr(artist: Artist):
    if hasattr(artist, CREATING_QUIB_NAME):
        delattr(artist, CREATING_QUIB_NAME)


def set_creating_quib(artist: Artist, quib: Optional[Quib]):
    if quib is None:
        delete_creating_quib_attr(artist)
    else:
        setattr(artist, CREATING_QUIB_NAME, quib)


def get_all_setter_quibs(artist: Artist) -> Dict[str, Quib]:
    if not hasattr(artist, SETTER_QUIBS_NAME):
        setattr(artist, SETTER_QUIBS_NAME, dict())
    return getattr(artist, SETTER_QUIBS_NAME)


def get_setter_quib(artist: Artist, name: str) -> Optional[Quib]:
    return get_all_setter_quibs(artist).get(name, None)


def set_setter_quib(artist: Artist, name: str, quib: Optional[Quib]):
    setter_quibs = get_all_setter_quibs(artist)
    if quib is None:
        setter_quibs.pop(name, None)
    else:
        setter_quibs[name] = quib


def delete_setting_quibs_attr(artist):
    if hasattr(artist, SETTER_QUIBS_NAME):
        delattr(artist, SETTER_QUIBS_NAME)


def clear_all_quibs(artist):
    delete_creating_quib_attr(artist)
    delete_setting_quibs_attr(artist)
