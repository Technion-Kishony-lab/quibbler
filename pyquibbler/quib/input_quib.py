from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Optional

from .assignment_template import AssignmentTemplate
from .quib import Quib
from .utils import is_there_a_quib_in_object
from ..env import is_debug
from ..exceptions import DebugException


@dataclass
class CannotNestQuibInIQuibException(DebugException):
    iquib: InputQuib

    def __str__(self):
        return 'Cannot create an input quib that contains another quib'


class InputQuib(Quib):
    def __init__(self, value: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Creates an InputQuib instance containing the given value.
        """
        super().__init__(assignment_template=assignment_template)
        self._value = value
        if is_debug():
            if is_there_a_quib_in_object(value, force_recursive=True):
                raise CannotNestQuibInIQuibException(self)

    def _override(self, key, value):
        """
        Override data inside the input quib.
        """
        self._value[key] = value

    def get_value(self):
        """
        No need to do any calculation, this is an input quib.
        """
        return self._value

    def _invalidate(self):
        """
        Input quibs are always valid, no need to do anything.
        """
        pass


iquib = InputQuib
