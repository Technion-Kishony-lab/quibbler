from __future__ import annotations

from typing import Optional, Dict, Set, TYPE_CHECKING
from matplotlib.artist import Artist

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


SETTER_QUIBS_NAME = '_quibbler_artist_setter_quibs'
CREATING_QUIB_NAME = '_quibbler_artist_creating_quib'
UPSTREAM_CALLER_QUIBS_NAME = '_quibbler_artist_upstream_caller_quibs'


def get_upstream_caller_quibs(artist: Artist) -> Set[Quib]:
    if not hasattr(artist, UPSTREAM_CALLER_QUIBS_NAME):
        setattr(artist, UPSTREAM_CALLER_QUIBS_NAME, set())
    return getattr(artist, UPSTREAM_CALLER_QUIBS_NAME)


def delete_upstream_caller_quibs_attr(artist: Artist):
    if hasattr(artist, UPSTREAM_CALLER_QUIBS_NAME):
        delattr(artist, UPSTREAM_CALLER_QUIBS_NAME)


def get_creating_quib(artist: Artist) -> Optional[Quib]:
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
    delete_upstream_caller_quibs_attr(artist)
