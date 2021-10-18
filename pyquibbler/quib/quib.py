from __future__ import annotations
import numpy as np
from functools import cached_property
from abc import ABC, abstractmethod
from dataclasses import dataclass
from operator import getitem
from typing import Set, Any, TYPE_CHECKING, Optional, Tuple, Type, List
from weakref import ref as weakref

from pyquibbler.exceptions import PyQuibblerException

from .assignment import AssignmentTemplate, RangeAssignmentTemplate, BoundAssignmentTemplate, Overrider, Assignment
from .utils import quib_method, Unpacker, recursively_run_func_on_object
from .assignment import PathComponent

if TYPE_CHECKING:
    from pyquibbler.quib.graphics import GraphicsFunctionQuib


@dataclass
class QuibIsNotNdArrayException(PyQuibblerException):
    quib: Quib
    value: Any

    def __str__(self):
        return f'The quib {self.quib} evaluates to {self.value}, which is not an ndarray, but a {type(self.value)}'


@dataclass
class OverridingNotAllowedException(PyQuibblerException):
    quib: Quib
    override: Assignment

    def __str__(self):
        return f'Cannot override {self.quib} with {self.override} as it does not allow overriding.'


class Quib(ABC):
    """
    An abstract class to describe the common methods and attributes of all quib types.
    """
    _DEFAULT_ALLOW_OVERRIDING = False

    def __init__(self,
                 assignment_template: Optional[AssignmentTemplate] = None,
                 allow_overriding: Optional[bool] = None):
        self._assignment_template = assignment_template
        # Can't use WeakSet because it can change during iteration
        self._children = set()
        self._overrider = Overrider()
        if allow_overriding is None:
            allow_overriding = self._DEFAULT_ALLOW_OVERRIDING
        self.allow_overriding = allow_overriding

    @property
    def children(self) -> Set[Quib]:
        """
        Return all valid children and clean up dead refs.
        """
        children = set()
        refs_to_remove = set()
        for child_ref in self._children:
            child = child_ref()
            if child is None:
                refs_to_remove.add(child_ref)
            else:
                children.add(child)
        for ref in refs_to_remove:
            self._children.remove(ref)
        return children

    def __get_children_recursively(self) -> Set[Quib]:
        children = self.children
        for child in self.children:
            children |= child.__get_children_recursively()
        return children

    def _get_graphics_function_quibs_recursively(self) -> Set[GraphicsFunctionQuib]:
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
        for graphics_function_quib in self._get_graphics_function_quibs_recursively():
            graphics_function_quib.get_value()

        axeses = set()
        for graphics_function_quib in self._get_graphics_function_quibs_recursively():
            for axes in graphics_function_quib.get_axeses():
                axeses.add(axes)
        for axes in axeses:
            redraw_axes(axes)

    def invalidate_and_redraw_at_path(self, path: Optional[List[PathComponent]] = None) -> None:
        """
        Perform all actions needed after the quib was mutated (whether by overriding or inverse assignment).
        If path is not given, the whole quib is invalidated.
        """
        if path is None:
            path = [PathComponent(component=..., indexed_cls=self.get_type())]
        self._invalidate_children_at_path(path)
        self.__redraw()

    def _invalidate_children_at_path(self, path: List[PathComponent]) -> None:
        """
        Change this quib's state according to a change in a dependency.
        """
        for child in self.children:
            child._invalidate_quib_with_children_at_path(self, path)

    def _get_path_for_children_invalidation(self, invalidator_quib: 'Quib',
                                            path: List['PathComponent']) -> List['PathComponent']:
        """
        Get the new path for invalidating children- a quib overrides this method if it has a specific way to translate
        paths to new invalidation paths.
        If not, invalidate all children all over; as you have no more specific way to invalidate them
        """
        return []

    def _invalidate_self(self):
        """
        This method is called whenever a quib itself is invalidated; subclasses will override this with their
        implementations for invalidations.
        For example, a simple implementation for a quib which is a function could be setting a boolean to true or
        false signifying validity
        """
        pass

    def _invalidate_quib_with_children_at_path(self, invalidator_quib, path: List[PathComponent]):
        """
        Invalidate a quib and it's children at a given path.
        This method should be overriden if there is any 'special' implementation for either invalidating oneself
        or for translating a path for invalidation
        """
        from .assignment.assignment import PathComponent
        if len(path) == 0:
            new_path = []
        else:
            new_path = self._get_path_for_children_invalidation(invalidator_quib, path)
        if new_path is not None:
            self._invalidate_self()
            self._invalidate_children_at_path(new_path)

    def add_child(self, quib: Quib) -> None:
        """
        Add the given quib to the list of quibs that are dependent on this quib.
        """
        # We used to give the ref a destruction callback that removed it from the children set,
        # but it could sometimes cause the set to change size during iteration.
        # So now we cleanup dead refs in the children property.
        self._children.add(weakref(quib))

    def __len__(self):
        return len(self.get_value())

    def __iter__(self):
        raise TypeError('Cannot iterate over quibs, as their size can vary. '
                        'Try Quib.iter_first() to iterate over the n-first items of the quib.')

    def override(self, assignment: Assignment, allow_overriding_from_now_on=True):
        """
        Overrides a part of the data the quib represents.
        """
        if allow_overriding_from_now_on:
            self.allow_overriding = True
        if not self.allow_overriding:
            raise OverridingNotAllowedException(self, assignment)
        self._overrider.add_assignment(assignment)

        self.invalidate_and_redraw_at_path(assignment.path)

    def remove_override(self, path: List[PathComponent]):
        """
        Remove overriding in a specific path in the quib.
        """
        self._overrider.remove_assignment(path)
        self.invalidate_and_redraw_at_path(path=path)

    def assign(self, assignment: Assignment) -> None:
        """
        Create an assignment with an Assignment object, overriding the current values at the assignment's paths with the
        assignment's value
        """
        self.override(assignment, allow_overriding_from_now_on=False)

    def assign_value(self, value: Any) -> None:
        """
        Helper method to assign a single value and override the whole value of the quib
        """
        from .assignment.assignment import PathComponent
        self.assign(Assignment(value=value,
                               path=[PathComponent(component=..., indexed_cls=self.get_type())]))

    def assign_value_to_key(self, key: Any, value: Any) -> None:
        """
        Helper method to assign a value at a specific key
        """
        from .assignment.assignment import PathComponent
        self.assign(Assignment(path=[PathComponent(component=key, indexed_cls=self.get_type())], value=value))

    def __getitem__(self, item):
        # We don't use the normal operator_overriding interface for two reasons:
        # 1. It can create issues with hinting in IDEs (for example, Pycharm will not recognize that Quibs have a
        # getitem and will issue a warning)
        # 2. We need the function to not be created dynamically as it needs to be in the inverser's supported functions
        # in order to be inversed correctly (and not simply override)
        from pyquibbler.quib import DefaultFunctionQuib
        from pyquibbler.quib.function_quibs.transpositional_function_quib import TranspositionalFunctionQuib
        return TranspositionalFunctionQuib.create(func=getitem, func_args=[self, item])

    def __setitem__(self, key, value):
        from .assignment.assignment import PathComponent
        self.assign(Assignment(value=value, path=[PathComponent(component=key, indexed_cls=self.get_type())]))

    def pretty_repr(self):
        """
        Returns a pretty representation of the quib. Might calculate values of parent quibs.
        """
        return repr(self)

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
    def _get_inner_value_valid_at_path(self, path: List[PathComponent]) -> Any:
        """
        Get the data this quib represents valid at the pat given, before applying quib features like overrides.
        Perform calculations if needed.
        """

    def get_value_valid_at_path(self, path: List[PathComponent]) -> Any:
        """
        Get the actual data that this quib represents, valid at the path given in the argument.
        The value will necessarily return in the shape of the actual result, but only the values at the given path
        are guaranteed to be valid
        """
        from pyquibbler.quib.graphics.global_collecting import QuibDependencyCollector
        QuibDependencyCollector.add_dependency(self)
        return self._overrider.override(self._get_inner_value_valid_at_path(path), self._assignment_template)

    def get_value(self) -> Any:
        """
        Get the entire actual data that this quib represents, all valid.
        This function might perform several different computations - function quibs
        are lazy, so a function quib might need to calculate uncached values and might
        even have to calculate the values of its dependencies.
        """
        from .assignment.assignment import PathComponent
        return self.get_value_valid_at_path([PathComponent(indexed_cls=self.get_type(), component=...)])

    def get_override_list(self) -> Overrider:
        """
        Returns an Overrider object representing a list of overrides performed on the quib.
        """
        return self._overrider

    def get_type(self) -> Type:
        """
        Get the type of wrapped value
        """
        return type(self.get_value_valid_at_path([]))

    @quib_method
    def get_shape(self) -> Tuple[int, ...]:
        """
        Assuming this quib represents a numpy ndarray, returns a quib of its shape.
        """
        value = self.get_value_valid_at_path([])
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
        return self._overrider.fill_override_mask(mask)

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

    def remove_child(self, quib_to_remove: Quib):
        """
        Removes a child from the quib, no longer sending invalidations to it
        """
        self._children.remove(weakref(quib_to_remove))

    @property
    @abstractmethod
    def parents(self) -> Set[Quib]:
        """
        Returns a list of quibs that this quib depends on.
        """

    @cached_property
    def ancestors(self) -> Set[Quib]:
        """
        Return all ancestors of the quib, going recursively up the tree
        """
        ancestors = set()
        for parent in self.parents:
            ancestors.add(parent)
            ancestors |= parent.ancestors
        return ancestors
