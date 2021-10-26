import contextlib
import functools
from dataclasses import dataclass
from typing import Any, Callable


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
class Mutable:
    val: Any

    def set(self, val: Any):
        self.val = val

    @contextlib.contextmanager
    def temporary_set(self, val):
        current = self.val
        self.set(val)
        try:
            yield
        finally:
            self.set(current)


@dataclass
class Flag(Mutable):

    def __bool__(self):
        return self.val
