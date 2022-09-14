import functools
from typing import Callable


def ensure_only_run_once_globally(func: Callable):
    """
    Decorator to ensure the function is only run once (globally)
    This does not raise an exception if the function is called twice
    """
    did_run = False

    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        nonlocal did_run
        if not did_run:
            res = func(*args, **kwargs)
            did_run = True
            return res

    return _wrapper


def assign_func_name(name: str):
    """
    Assign the __name__ property of a function.
    """

    def _assign(func):
        func.__name__ = name
        return func

    return _assign