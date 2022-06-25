from pyquibbler.utils import StrEnum


class CacheMode(StrEnum):
    """
    The different modes of quib caching.

    Dictates whether a quib should cache its function result, to avoid recalculations on repeated calls.

    Options are listed below (Attributes).

    Note
    ----
    Quibs with random functions and graphics quibs are always cached even when cache mode is ``'off'``.

    See Also
    --------
    Quib.cache_mode, CacheStatus
    """
    AUTO = 'auto'
    "Caching is decided automatically according to the ratio between evaluation time and memory consumption."

    OFF = 'off'
    "Do not cache, unless the quib's function is random or graphics (``'off'``)."

    ON = 'on'
    "Always cache (``'on'``)."
