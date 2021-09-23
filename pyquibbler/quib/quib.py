from abc import ABC, abstractmethod
from functools import reduce
from operator import or_
from typing import Set
from weakref import ref as weakref

from pyquibbler.graphics import ArtistsRedrawer, redraw_axes


class Quib(ABC):
    """
    An abstract class to describe the common methods and attributes of all quib types.
    """

    def __init__(self, artists_redrawers: Set[ArtistsRedrawer], children: Set[weakref]):
        self._artists_redrawers = artists_redrawers
        self._children = children

    def __invalidate_children(self):
        """
        Notify this quib's dependents that the data in this quib has changed.
        This should be called every time the quib is changed.
        """
        for child in self._children:
            child()._invalidate()

    def __get_artists_redrawers_recursively(self):
        """
        Get all artists that directly or indirectly depend on this quib.
        """
        return reduce(or_, (child().__get_artists_redrawers_recursively()
                            for child in self._children), self._artists_redrawers)

    def __redraw(self):
        """
        Redraw all artists that directly or indirectly depend on this quib.
        """
        for artists_redrawer in self.__get_artists_redrawers_recursively():
            artists_redrawer.redraw(redraw_in_gui=False)

        axeses = set()
        for artists_redrawer in self.__get_artists_redrawers_recursively():
            for axes in artists_redrawer.get_axeses():
                axeses.add(axes)
        for axes in axeses:
            redraw_axes(axes)

    def invalidate_and_redraw(self):
        """
        Perform all actions needed after the quib was mutated (whether by overriding or reverse assignment).
        """
        self.__invalidate_children()
        self.__redraw()

    @abstractmethod
    def _invalidate(self):
        """
        Change this quib's state according to a change in a dependency.
        """

    @abstractmethod
    def get_value(self):
        """
        Get the actual data that this quib represents.
        This function might perform several different calculations - function quibs
        are lazy, so a function quib might need to calculate uncached values and might
        even have to calculate the values of its dependencies.
        """

    def add_artists_redrawer(self, artists_redrawer):
        """
        Add the given artist to this quib's direct artists.
        """
        self._artists_redrawers.add(artists_redrawer)

    def add_child(self, quib):
        """
        Add the given quib to the list of quibs that are dependent on this quib.
        """
        self._children.add(weakref(quib, lambda ref: self._children.remove(ref)))

    def __len__(self):
        return len(self.get_value())

    def __copy__(self):
        return self

    def __deepcopy__(self, memodict={}):
        return self

    def __iter__(self):
        raise TypeError('Cannot iterate over quibs, as their size can vary')
