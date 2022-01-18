import numpy as np
from abc import ABC, abstractmethod
from math import floor
from typing import Any, Type
from dataclasses import dataclass

from pyquibbler.exceptions import DebugException, PyQuibblerException
from pyquibbler.utilities.input_validation_utils import InvalidArgumentException

CONSTRUCTORS = {
    np.ndarray: np.array
}


@dataclass
class InvalidTypeException(PyQuibblerException):
    type_: Type

    def __str__(self):
        return f"The type {repr(self.type_)} is incompatible with the given assignment template "


@dataclass
class BoundMaxBelowMinException(DebugException):
    minimum: Any
    maximum: Any

    def __str__(self):
        return f'Maximum ({self.maximum} is smaller than minimum ({self.minimum})'


@dataclass
class RangeStopBelowStartException(DebugException):
    start: Any
    stop: Any

    def __str__(self):
        return f'Stop ({self.stop} is smaller than start ({self.start})'


@dataclass
class TypesMustBeSameInAssignmentTemplateException(DebugException):

    def __str__(self):
        return 'You cannot have different types in your assignment template'


def get_number_in_bounds(number, minimum, maximum):
    return min(max(number, minimum), maximum)


@dataclass
class AssignmentTemplate(ABC):
    @abstractmethod
    def _convert_number(self, number: Any):
        """
        Convert the given object to match the template.
        """

    @abstractmethod
    def _get_number_type(self) -> Type:
        pass

    def convert(self, data: Any):
        """
        Convert the given data according to the assignment template.
        Assignment templates work on numbers, so if the data is iterable, its items will be converted recursively.
        This is useful in cases like the following:
        ```
        iquib(np.arange(5))[[1, 2, 3]] = [1, 2, 3]
        iquib(np.zeros((2, 2)))[0] = [1, 1]
        ```
        """
        # we need to be careful of strings, as they are iterators but not valid values
        if isinstance(data, str):
            raise InvalidTypeException(str)

        try:
            iterator = iter(data)
        except TypeError:
            constructor = CONSTRUCTORS.get(self._get_number_type(), self._get_number_type())
            casted_data = constructor(data)
            return self._convert_number(casted_data)
        else:
            return [self.convert(item) for item in iterator]


@dataclass
class BoundAssignmentTemplate(AssignmentTemplate):
    """
    Limits assigned number to specific minimum and maximum bounds.
    """
    minimum: Any
    maximum: Any

    def __post_init__(self):
        if self.maximum < self.minimum:
            raise BoundMaxBelowMinException(self.minimum, self.maximum)

        if type(self.minimum) != type(self.maximum): # noqa
            raise TypesMustBeSameInAssignmentTemplateException()

    def _get_number_type(self) -> Type:
        return type(self.minimum)

    def _convert_number(self, number):
        return get_number_in_bounds(number, self.minimum, self.maximum)


@dataclass
class RangeAssignmentTemplate(AssignmentTemplate):
    """
    Limits assigned number to a given range.
    """

    start: Any
    stop: Any
    step: Any

    def __post_init__(self):
        if self.stop < self.start:
            raise RangeStopBelowStartException(self.start, self.stop)
        if (type(self.start) != type(self.stop)) or (type(self.start) != type(self.step)): # noqa
            raise TypesMustBeSameInAssignmentTemplateException()

    def _get_number_type(self) -> Type:
        return type(self.start)

    def _convert_number(self, number: Any):
        rounded = round((number - self.start) / self.step)
        bound = get_number_in_bounds(rounded, 0, floor((self.stop - self.start) / self.step))
        constructor = CONSTRUCTORS.get(type(number), type(number))
        return constructor(self.start + bound * self.step)


def create_assignment_template(*args):
    if len(args) == 1 and isinstance(args[0], tuple):
        args = args[0]

    if len(args) == 1:
        if not isinstance(args[0], AssignmentTemplate):
            raise InvalidArgumentException(expected_type=(AssignmentTemplate, tuple),
                                           var_name="assignment template")
        template, = args
    elif len(args) == 2:
        minimum, maximum = args
        template = BoundAssignmentTemplate(minimum, maximum)
    elif len(args) == 3:
        start, stop, step = args
        template = RangeAssignmentTemplate(start, stop, step)
    else:
        raise TypeError('Unsupported number of arguments, see docstring for usage')

    return template