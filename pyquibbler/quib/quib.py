from abc import ABC, abstractmethod
from functools import reduce
from operator import or_
from weakref import ref as weakref


class Quib(ABC):
    """
    An abstract class to describe the common methods and attributes of all quib types.
    """

    def __init__(self):
        self._children = set()

    def __invalidate_children_recursively(self):
        """
        Notify this quib's dependents that the data in this quib has changed.
        This should be called every time the quib is changed.
        """
        for child in self.get_children_recursively():
            child()._invalidate()

    def get_children_recursively(self):
        return reduce(or_, (child().get_children_recursively()
                            for child in self._children), set(self._children))

    def __get_graphics_function_quibs_recursively(self):
        """
        Get all artists that directly or indirectly depend on this quib.
        """
        from pyquibbler.quib.graphics import GraphicsFunctionQuib
        return {child for child in self.get_children_recursively() if isinstance(child(), GraphicsFunctionQuib)}

    def __redraw(self):
        """
        Redraw all artists that directly or indirectly depend on this quib.
        """
        from pyquibbler.quib.graphics import redraw_axes
        for graphics_function_quib in self.__get_graphics_function_quibs_recursively():
            graphics_function_quib().get_value()

        axeses = set()
        for graphics_function_quib in self.__get_graphics_function_quibs_recursively():
            for axes in graphics_function_quib().get_axeses():
                axeses.add(axes)
        for axes in axeses:
            redraw_axes(axes)

    def invalidate_and_redraw(self):
        """
        Perform all actions needed after the quib was mutated (whether by overriding or reverse assignment).
        """
        self.__invalidate_children_recursively()
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
