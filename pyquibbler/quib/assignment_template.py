from abc import ABC, abstractmethod
from math import floor
from typing import Callable, Any
from dataclasses import dataclass

from pyquibbler.exceptions import DebugException


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


def get_number_in_bounds(number, minimum, maximum):
    return min(max(number, minimum), maximum)


@dataclass
class AssignmentTemplate(ABC):
    @abstractmethod
    def convert(self, data):
        """
        Convert the given object to match the template.
        """


@dataclass
class BoundAssinmentTemplate(AssignmentTemplate):
    """
    Limits assigned data to specific minimum and maximum bounds.
    """
    minimum: Any
    maximum: Any

    def __post_init__(self):
        if self.maximum < self.minimum:
            raise BoundMaxBelowMinException(self.minimum, self.maximum)

    def convert(self, data):
        return get_number_in_bounds(data, self.minimum, self.maximum)


@dataclass
class RangeAssignmentTemplate(AssignmentTemplate):
    """
    Limits assigned data to a given range.
    """

    start: Any
    stop: Any
    step: Any

    def __post_init__(self):
        if self.stop < self.start:
            raise RangeStopBelowStartException(self.start, self.stop)

    def convert(self, data):
        rounded = round((data - self.start) / self.step)
        bound = get_number_in_bounds(rounded, 0, floor((self.stop - self.start) / self.step))
        return type(data)(self.start + bound * self.step)
