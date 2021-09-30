from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Set, Any, TYPE_CHECKING, Optional
from weakref import ref as weakref

from .assignment_template import AssignmentTemplate, RangeAssignmentTemplate, BoundAssignmentTemplate

if TYPE_CHECKING:
    from pyquibbler.quib.graphics import GraphicsFunctionQuib


class Quib(ABC):
    """
    An abstract class to describe the common methods and attributes of all quib types.
    """

    def __init__(self, assignment_template: Optional[AssignmentTemplate] = None):
        self._assignment_template = assignment_template
        self._children = set()

    def __invalidate_children_recursively(self) -> None:
        """
        Notify this quib's dependents that the data in this quib has changed.
        This should be called every time the quib is changed.
        """
        for child in self.__get_children_recursively():
            child._invalidate()

    def __get_children_recursively(self) -> Set[Quib]:
        children = {child_ref() for child_ref in self._children}
        for child_ref in self._children:
            children |= child_ref().__get_children_recursively()
        return children

    def __get_graphics_function_quibs_recursively(self) -> Set[GraphicsFunctionQuib]:
        """
        Get all artists that directly or indirectly depend on this quib.
        """
        from pyquibbler.quib.graphics import GraphicsFunctionQuib
        return {child for child in self.__get_children_recursively() if isinstance(child, GraphicsFunctionQuib)}

    def __redraw(self) -> None:
        """
        Redraw all artists that directly or indirectly depend on this quib.
        """
        from pyquibbler.quib.graphics import redraw_axes
        for graphics_function_quib in self.__get_graphics_function_quibs_recursively():
            graphics_function_quib.get_value()

        axeses = set()
        for graphics_function_quib in self.__get_graphics_function_quibs_recursively():
            for axes in graphics_function_quib.get_axeses():
                axeses.add(axes)
        for axes in axeses:
            redraw_axes(axes)

    def invalidate_and_redraw(self) -> None:
        """
        Perform all actions needed after the quib was mutated (whether by overriding or reverse assignment).
        """
        self.__invalidate_children_recursively()
        self.__redraw()

    @abstractmethod
    def _invalidate(self) -> None:
        """
        Change this quib's state according to a change in a dependency.
        """

    @abstractmethod
    def get_value(self) -> Any:
        """
        Get the actual data that this quib represents.
        This function might perform several different calculations - function quibs
        are lazy, so a function quib might need to calculate uncached values and might
        even have to calculate the values of its dependencies.
        """

    def add_child(self, quib: Quib) -> None:
        """
        Add the given quib to the list of quibs that are dependent on this quib.
        """
        self._children.add(weakref(quib, lambda ref: self._children.remove(ref)))

    def __len__(self):
        return len(self.get_value())

    def __copy__(self):
        return self

    def __deepcopy__(self, memodict):
        return self

    def __iter__(self):
        raise TypeError('Cannot iterate over quibs, as their size can vary')

    @abstractmethod
    def _override(self, key, value):
        """
        Overrides a part of the data the quib represents.
        """

    def __setitem__(self, key, value):
        if self._assignment_template is not None:
            value = self._assignment_template.convert(value)
        self._override(key, value)
        self.invalidate_and_redraw()

    def get_assignment_template(self) -> AssignmentTemplate:
        return self._assignment_template

    def set_assignment_template(self, *args) -> None:
        """
        Sets an assignment template for the quib.
        Usage:

        - quib.set_assignment_template(assignment_template): set a specific AssignmentTemplate object.
        - quib.set_assignment_template(min, max): set the template to a bound template between min and max.
        - quib.set_assignment_template(start, stop, step): set the template to a bound template between min and max.
        """
        if len(args) == 1:
            template, = args
        elif len(args) == 2:
            minimum, maximum = args
            template = BoundAssignmentTemplate(minimum, maximum)
        elif len(args) == 3:
            start, stop, step = args
            template = RangeAssignmentTemplate(start, stop, step)
        else:
            raise TypeError('Unsupported number of arguments, see docstring for usage')
        self._assignment_template = template
