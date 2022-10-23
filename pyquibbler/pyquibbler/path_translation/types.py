from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import numpy as np

from .exceptions import FailedToTranslateException


@dataclass(frozen=True)
class Source:
    value: Any

    def __hash__(self):
        return hash(id(self))


class NoMetadataSource(Source):

    # We have an empty init in order to override the default Source __init__ which has `value` in it's `__init__`
    def __init__(self):
        pass

    @property
    def value(self):
        """
        If anyone accesses value, we want to immediately raise a known exception so that the translator will fail-
        in order for a translator to work WITHOUT metadata of parents, it needs to NEVER access the value of it's
        sources (as nothing is known about them)
        """
        raise FailedToTranslateException()

    def __repr__(self):
        return f"<{self.__class__.__name__}>"


@dataclass
class Inversal:
    assignment: Any
    source: Source

    def cast_assigned_value_by_source_value(self):
        if len(self.assignment.path):
            return

        original_value = self.source.value
        if isinstance(original_value, np.ndarray):
            self.assignment.value = np.array(self.assignment.value, dtype=original_value.dtype)
        else:
            self.assignment.value = type(original_value)(self.assignment.value)
