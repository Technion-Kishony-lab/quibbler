from pyquibbler.utilities.basic_types import StrEnum


class CacheMode(StrEnum):
    """
    Modes of quib caching.

    Dictates whether a quib should cache its function result, to avoid recalculations on repeated calls.

    Options are listed below (see Attributes).

    Note
    ----
    Quibs with random functions and graphics quibs are always cached (even with cache mode set to ``'off'``).

    See Also
    --------
    Quib.cache_mode, CacheStatus
    """
    AUTO = 'auto'
    "Auto cache decision based on the ratio between evaluation time and memory consumption (``'auto'``)."

    OFF = 'off'
    "Do not cache, unless the quib's function is random or graphics (``'off'``)."

    ON = 'on'
    "Always cache (``'on'``)."
