from pyquibbler.utils import StrEnum


class CachingOptions(StrEnum):
    """
    The different modes in which the caching of a Quib can operate:
        'auto':     Caching is decided automatically according to the ratio between evaluation time and
                    memory consumption. Quibs with random or graphics functions are always cached.
        'on':       Always cache.
        'off':      Do not cache, unless the quib's function is random or graphics.
    """

    AUTO = 'auto'
    OFF = 'off'
    ON = 'on'
