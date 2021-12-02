from dataclasses import dataclass
from enum import Enum

from pyquibbler.exceptions import PyQuibblerException


@dataclass
class UnknownCacheBehaviorException(PyQuibblerException):
    attempted_value: str

    def __str__(self):
        return f"{self.attempted_value} is not a valid value for a cache behavior"


class CacheBehavior(Enum):
    """
    The different modes in which the caching of a FunctionQuib can operate:
     - `AUTO`: decide automatically according to the ratio between evaluation time and memory consumption.
     - `OFF`: never cache.
     - `ON`: always cache.
    """
    AUTO = 'auto'
    OFF = 'off'
    ON = 'on'

