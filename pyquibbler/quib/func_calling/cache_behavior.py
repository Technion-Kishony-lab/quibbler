from pyquibbler.utils import StrEnum


class CacheBehavior(StrEnum):
    """
    The different modes in which the caching of a FuncQuib can operate:
     - `AUTO`: decide automatically according to the ratio between evaluation time and memory consumption.
     - `OFF`: never cache.
     - `ON`: always cache.
    """
    AUTO = 'auto'
    OFF = 'off'
    ON = 'on'
