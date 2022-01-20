import contextlib
import functools
import inspect
from typing import Callable, Any, Tuple, Mapping
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


def convert_args_and_kwargs(converter: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Apply the given converter on all given arg and kwarg values.
    """
    return (tuple(converter(i, val) for i, val in enumerate(args)),
            {name: converter(name, val) for name, val in kwargs.items()})


@functools.lru_cache()
def get_signature_for_func(func):
    return inspect.signature(func)
