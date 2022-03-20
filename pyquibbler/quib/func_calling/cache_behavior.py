from dataclasses import dataclass
from enum import Enum

from pyquibbler.exceptions import PyQuibblerException


class CacheBehavior(str, Enum):
    """
    The different modes in which the caching of a FuncQuib can operate:
     - `AUTO`: decide automatically according to the ratio between evaluation time and memory consumption.
     - `OFF`: never cache.
     - `ON`: always cache.
    """
    AUTO = 'auto'
    OFF = 'off'
    ON = 'on'
