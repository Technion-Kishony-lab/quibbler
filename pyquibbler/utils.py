import contextlib
import functools
from typing import Callable
from dataclasses import dataclass


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


@dataclass
class Flag:
    is_set: bool

    def set(self, val: bool):
        self.is_set = val

    def __bool__(self):
        return self.is_set

    @contextlib.contextmanager
    def temporary_set(self, val: bool):
        current = self.is_set
        self.set(val)
        yield
        self.set(current)
