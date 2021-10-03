from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Set, Any, TYPE_CHECKING, Optional, Tuple
from weakref import ref as weakref

import numpy as np

from pyquibbler.exceptions import PyQuibblerException
from .assignment import AssignmentTemplate, RangeAssignmentTemplate, BoundAssignmentTemplate, Overrider, Assignment
from .utils import deep_copy_without_quibs_or_artists, quib_method

if TYPE_CHECKING:
    from pyquibbler.quib.graphics import GraphicsFunctionQuib


@dataclass
class QuibIsNotNdArrayException(PyQuibblerException):
    quib: Quib
    value: Any

    def __str__(self):
        return f'The quib {self.quib} evaluates to {self.value}, which is not an ndarray'


class Quib(ABC):
    """
    An abstract class to describe the common methods and attributes of all quib types.
    """

    def __init__(self, assignment_template: Optional[AssignmentTemplate] = None):
        self._assignment_template = assignment_template
        self._children = set()
        self._overrider = Overrider()

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

    def add_child(self, quib: Quib) -> None:
        """
        Add the given quib to the list of quibs that are dependent on this quib.
        """
        self._children.add(weakref(quib, lambda ref: self._children.remove(ref)))

    def __len__(self):
        return len(self.get_value())

    def __iter__(self):
        raise TypeError('Cannot iterate over quibs, as their size can vary')

    def _override(self, key, value):
        """
        Overrides a part of the data the quib represents.
        """
        self._overrider.add_assignment(Assignment(key, value))

    def __setitem__(self, key: Any, value: Any) -> None:
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

    @abstractmethod
    def _get_inner_value(self) -> Any:
        """
        Get the data this quib represents, before applying quib features like overrides.
        Perform calculations if needed.
        """

    def get_value(self) -> Any:
        """
        Get the actual data that this quib represents.
        This function might perform several different computations - function quibs
        are lazy, so a function quib might need to calculate uncached values and might
        even have to calculate the values of its dependencies.
        """
        value = deep_copy_without_quibs_or_artists(self._get_inner_value())
        self._overrider.override(value, self._assignment_template)
        return value

    def get_override_list(self) -> Overrider:
        """
        Returns an Overrider object representing a list of overrides performed on the quib.
        """
        return self._overrider

    @quib_method
    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        value = self.get_value()
        if not isinstance(value, np.ndarray):
            raise QuibIsNotNdArrayException(self, value)
        return value.shape

    def get_override_mask(self) -> np.ndarray:
        """
        Assuming this quib represents a numpy ndarray, returns a boolean array of the same shape.
        Every value in that array is set to True if the matching value in the array is overridden, and False otherwise.
        """
        shape = self.get_shape().get_value()
        mask = np.zeros(shape, dtype=np.bool)
        # Can't use `mask[all_keys] = True` trivially, because some of the keys might be lists themselves.
        for assignment in self._overrider:
            mask[assignment.key] = True
        return mask
