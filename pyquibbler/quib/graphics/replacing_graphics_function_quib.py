from itertools import chain
from typing import Optional
from matplotlib.artist import Artist

from pyquibbler.quib import GraphicsFunctionQuib
from pyquibbler.quib.utils import iter_object_type_in_args


class ReplacingGraphicsFunctionQuib(GraphicsFunctionQuib):
    """
    This quib will replace all previous instances of her same type on the artists she is set
    """

    def _remove_previous_quib_from_parents(self, previous_quib: 'ReplacingGraphicsFunctionQuib'):
        for parent in previous_quib.parents:
            parent.remove_child(previous_quib)

    def persist_self_on_artists(self):
        for artist in chain(self._artists, iter_object_type_in_args(Artist, self.args, self.kwargs)):
            name = f'_quibbler_{self.func.__name__}'
            current_quib: Optional['ReplacingGraphicsFunctionQuib'] = getattr(artist, name, None)
            if current_quib is not None:
                self._remove_previous_quib_from_parents(current_quib)
            setattr(artist, name, self)
