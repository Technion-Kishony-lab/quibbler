import numpy as np
from abc import ABC, abstractmethod
from dataclasses import dataclass

from typing import Any, Type

from pyquibbler.exceptions import DebugException, PyQuibblerException
from pyquibbler.utilities.input_validation_utils import InvalidArgumentTypeException
from pyquibbler.utilities.iterators import recursively_run_func_on_object

from .rounding import round_to_num_digits, number_of_digits

CONSTRUCTORS = {
    np.ndarray: np.array
}


@dataclass
class InvalidTypeException(PyQuibblerException):
    type_: Type

    def __str__(self):
        return f"The type {repr(self.type_)} is incompatible with the given assignment template."


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
    return np.minimum(np.maximum(number, minimum), maximum)


@dataclass
class AssignmentTemplate(ABC):
    """
    Convert an assignment to a quib according to specified type and range constraints

    See Also
    --------
    Quib.assignment_template
    Quib.set_assignment_template
    """

    @abstractmethod
    def _convert_number(self, number: Any):
        """
        Convert the given object to match the template.
        """

    @abstractmethod
    def _get_number_type(self) -> Type:
        pass

    def _convert_and_cast_number(self, data):
        try:
            if not (isinstance(data, (np.ndarray, int, float)) or np.issubdtype(data, np.number)):
                raise InvalidTypeException(type(data))
        except TypeError:
            raise InvalidTypeException(type(data))

        data = self._convert_number(data)
        if isinstance(data, np.ndarray):
            casted_data = np.ndarray.astype(data, self._get_number_type())
        else:
            constructor = CONSTRUCTORS.get(self._get_number_type(), self._get_number_type())
            casted_data = constructor(data)
        return casted_data

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
        return recursively_run_func_on_object(self._convert_and_cast_number, data)


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

    def _convert_number(self, number: Any):
        return get_number_in_bounds(number, self.minimum, self.maximum)


@dataclass
class RangeAssignmentTemplate(AssignmentTemplate):
    """
    Limits assigned number to a given range.
    """

    start: Any
    stop: Any
    step: Any
    _num_digits: int = None

    def __post_init__(self):
        if self.stop < self.start:
            raise RangeStopBelowStartException(self.start, self.stop)
        if (type(self.start) != type(self.stop)) or (type(self.start) != type(self.step)): # noqa
            raise TypesMustBeSameInAssignmentTemplateException()
        self._num_digits = max(number_of_digits(self.start), number_of_digits(self.stop), number_of_digits(self.step))

    def _get_number_type(self) -> Type:
        return type(self.start)

    def _convert_number(self, number: Any):
        num_steps = np.round((number - self.start) / self.step)
        max_steps = np.floor((self.stop - self.start) / self.step)
        bound_num_steps = get_number_in_bounds(num_steps, 0, max_steps)
        value = self.start + bound_num_steps * self.step

        # to prevent: RangeAssignmentTemplate(0., 1., 0.01).convert(np.log(2)) -> 0.6900000000000001
        value = round_to_num_digits(value, self._num_digits)
        return value


def create_assignment_template(*args):
    """
    Create an AssignmentTemplate with a type dependent on number of args.

    (template) -> template
    (min, max) -> BoundAssignmentTemplate(min, max)
    (start, stop, step) -> RangeAssignmentTemplate(start, stop, step)
    """
    if len(args) == 1 and isinstance(args[0], tuple):
        args = args[0]

    if len(args) == 1:
        if not isinstance(args[0], (AssignmentTemplate, type(None))):
            raise InvalidArgumentTypeException(expected_type=(AssignmentTemplate, tuple),
                                               var_name="assignment_template")
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
