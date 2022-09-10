import contextlib
from typing import Any
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


class StrEnum(str, Enum):
    pass
