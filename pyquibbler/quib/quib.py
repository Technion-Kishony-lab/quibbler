from __future__ import annotations
import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass
from operator import getitem
from typing import Set, Any, TYPE_CHECKING, Optional, Tuple, Type
from weakref import ref as weakref

from pyquibbler.exceptions import PyQuibblerException

from .assignment import AssignmentTemplate, RangeAssignmentTemplate, BoundAssignmentTemplate, Overrider, Assignment
from .assignment.overrider import deep_assign_data_with_paths
from .utils import quib_method, Unpacker, recursively_run_func_on_object

if TYPE_CHECKING:
    from pyquibbler.quib.graphics import GraphicsFunctionQuib


@dataclass
class QuibIsNotNdArrayException(PyQuibblerException):
    quib: Quib
    value: Any

    def __str__(self):
        return f'The quib {self.quib} evaluates to {self.value}, which is not an ndarray'


@dataclass
class OverridingNotAllowedException(PyQuibblerException):
    pass


class Quib(ABC):
    """
    An abstract class to describe the common methods and attributes of all quib types.
    """
    _DEFAULT_ALLOW_OVERRIDING = False

    def __init__(self,
                 assignment_template: Optional[AssignmentTemplate] = None,
                 allow_overriding: Optional[bool] = None):
        self._assignment_template = assignment_template
        self._children = set()
        self._overrider = Overrider()
        if allow_overriding is None:
            allow_overriding = self._DEFAULT_ALLOW_OVERRIDING
        self.allow_overriding = allow_overriding

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

    def __hash__(self):
        return id(self)

    def __len__(self):
        return len(self.get_value())

    def __iter__(self):
        raise TypeError('Cannot iterate over quibs, as their size can vary. '
                        'Try Quib.iter_first() to iterate over the n-first items of the quib.')

    def _override(self, assignment: Assignment):
        """
        Overrides a part of the data the quib represents.
        """
        # This is not an exception, if this function is called while overriding is not allowed then we have a bug
        assert self.allow_overriding
        self._overrider.add_assignment(assignment)
        self.invalidate_and_redraw()

    def assign(self, assignment: Assignment) -> None:
        """
        Create an assignment with an Assignment object, overriding the current values at the assignment's paths with the
        assignment's value
        """
        if not self.allow_overriding:
            raise OverridingNotAllowedException()
        self._override(assignment)

    def assign_value(self, value: Any) -> None:
        """
        Helper method to assign a single value and override the whole value of the quib
        """
        self.assign(Assignment(value=value, paths=[...]))

    def assign_value_to_key(self, key: Any, value: Any) -> None:
        """
        Helper method to assign a value at a specific key
        """
        self.assign(Assignment(paths=[key], value=value))

    def __getitem__(self, item):
        # We don't use the normal operator_overriding interface for two reasons:
        # 1. It can create issues with hinting in IDEs (for example, Pycharm will not recognize that Quibs have a
        # getitem and will issue a warning)
        # 2. We need the function to not be created dynamically as it needs to be in the reverser's supported functions
        # in order to be reversed correctly (and not simply override)
        from pyquibbler.quib import DefaultFunctionQuib
        return DefaultFunctionQuib.create(func=getitem, func_args=[self, item])

    def __setitem__(self, key, value):
        self.assign(Assignment(value=value, paths=[key]))

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
        return self._overrider.override(self._get_inner_value(), self._assignment_template)

    def get_override_list(self) -> Overrider:
        """
        Returns an Overrider object representing a list of overrides performed on the quib.
        """
        return self._overrider

    def get_type(self) -> Type:
        """
        Get the type of wrapped value
        """
        return type(self.get_value())

    @quib_method
    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        value = self.get_value()
        if not isinstance(value, np.ndarray):
            if isinstance(value, list):
                return np.array(value, dtype=object).shape
            # We, like numpy, consider this a zero dimensional array
            return tuple()
        return value.shape

    @quib_method
    def _get_override_mask(self, shape: Tuple[int, ...]) -> np.ndarray:
        """
        Return an override mask based on assignments in self._overrider, in the given shape.
        This is an internal method so when called with a quib instead of the shape, the resulting quib
        will be dependent on both self and the shape quib.
        """
        if issubclass(self.get_type(), np.ndarray):
            mask = np.zeros(shape, dtype=np.bool)
        else:
            mask = recursively_run_func_on_object(func=lambda x: False, obj=self.get_value())
        # Can't use `mask[all_keys] = True` trivially, because some of the keys might be lists themselves.
        for assignment in self._overrider:
            mask = deep_assign_data_with_paths(paths=assignment.paths, value=True, data=mask)
        return mask

    def get_override_mask(self) -> Quib:
        """
        Assuming this quib represents a numpy ndarray, return a quib representing its override mask.
        The override mask is a boolean array of the same shape, in which every value is
        set to True if the matching value in the array is overridden, and False otherwise.
        """
        return self._get_override_mask(self.get_shape())

    def iter_first(self, amount: Optional[int] = None):
        """
        Returns an iterator to the first `amount` elements of the quib.
        `a, b = quib.iter_first(2)` is the same as `a, b = quib[0], quib[1]`.
        When `amount` is not given, quibbler will try to detect the correct amount automatically, and
        might fail with a RuntimeError.
        For example, `a, b = iquib([1, 2]).iter_first()` is the same as `a, b = iquib([1, 2]).iter_first(2)`.
        But note that even if the quib is larger than the unpacked amount, the iterator will still yield only the first
        items - `a, b = iquib([1, 2, 3, 4]).iter_first()` is the same as `a, b = iquib([1, 2, 3, 4]).iter_first(2)`.
        """
        return Unpacker(self, amount)
