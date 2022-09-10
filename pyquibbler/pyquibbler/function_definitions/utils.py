import functools
import inspect


@functools.lru_cache()
def get_signature_for_func(func):
    """
    Get the signature for a function- the reason we use this instead of immediately going to inspect is in order to
    cache the result per function
    """
    return inspect.signature(func)
