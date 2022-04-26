import dataclasses
from typing import Optional, Dict
from matplotlib.artist import Artist

from pyquibbler.quib.quib import Quib


@dataclasses.dataclass
class QuibblerArtistWrapper:
    artist: Artist

    SETTER_QUIBS_NAME = '_quibbler_artist_setter_quibs'
    CREATING_QUIB_NAME = '_quibbler_artist_creating_quib'

    def get_creating_quib(self):
        return getattr(self.artist, self.CREATING_QUIB_NAME, None)

    def delete_creating_quib_attr(self):
        if hasattr(self.artist, self.CREATING_QUIB_NAME):
            delattr(self.artist, self.CREATING_QUIB_NAME)

    def set_creating_quib(self, quib: Optional[Quib]):
        if quib is None:
            self.delete_creating_quib_attr()
        else:
            setattr(self.artist, self.CREATING_QUIB_NAME, quib)

    def get_all_setter_quibs(self) -> Dict[str, Quib]:
        if not hasattr(self.artist, self.SETTER_QUIBS_NAME):
            setattr(self.artist, self.SETTER_QUIBS_NAME, dict())
        return getattr(self.artist, self.SETTER_QUIBS_NAME)

    def get_setter_quib(self, name: str) -> Optional[Quib]:
        return self.get_all_setter_quibs().get(name, None)

    def set_setter_quib(self, name: str, quib: Optional[Quib]):
        setter_quibs = self.get_all_setter_quibs()
        if quib is None:
            setter_quibs.pop(name, None)
        else:
            setter_quibs[name] = quib

    def delete_setting_quibs_attr(self):
        if hasattr(self.artist, self.SETTER_QUIBS_NAME):
            delattr(self.artist, self.SETTER_QUIBS_NAME)

    def clear_all_quibs(self):
        self.delete_creating_quib_attr()
        self.delete_setting_quibs_attr()
