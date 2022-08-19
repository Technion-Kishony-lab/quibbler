import contextlib
import functools
import inspect
from typing import Callable, Any, Tuple, Mapping
from dataclasses import dataclass
from enum import Enum


class Singleton(object):
    """
    A base class for allowing only one instance
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not isinstance(cls._instance, cls):
            cls._instance = object.__new__(cls, *args, **kwargs)
        return cls._instance


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

    def __eq__(self, other):
        return self.val == other

    def __ne__(self, other):
        return self.val != other


def convert_args_and_kwargs(converter: Callable, args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Apply the given converter on all given arg and kwarg values.
    """
    return (tuple(converter(i, val) for i, val in enumerate(args)),
            {name: converter(name, val) for name, val in kwargs.items()})


@functools.lru_cache()
def get_signature_for_func(func):
    """
    Get the signature for a function- the reason we use this instead of immediately going to inspect is in order to
    cache the result per function
    """
    return inspect.signature(func)


class StrEnum(str, Enum):
    pass


def get_original_func(func: Callable):
    """
    Get the original func- if this function is already overrided, get the original func it's function_definitions.

    So for example, if the OVERLOADED np.array is given as `func`, then the ORIGINAL np.array will be returned
    If the ORIGINAL np.array is given as `func`, then `func` will be returned
    """
    while hasattr(func, '__quibbler_wrapped__'):
        func = func.__quibbler_wrapped__
    return func
