from __future__ import annotations

import contextlib
from typing import Set, TYPE_CHECKING

from pyquibbler.exceptions import PyQuibblerException

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

QUIB_GUARDS = []


def is_within_quib_guard():
    return len(QUIB_GUARDS) > 0


def get_current_quib_guard():
    return QUIB_GUARDS[-1]


class CannotAccessQuibInScopeException(PyQuibblerException):

    def __str__(self):
        return "You cannot access quibs from the global scope within a user function"


class AnotherQuibGuardIsAlreadyActiveException(PyQuibblerException):
    def __str__(self):
        return "There cannot be two quib guards at once"


class QuibGuard:
    """
    A quib guard allows you to specify places in which only certain quibs (and their recursive children)
    are allowed to be accessed
    """
    def __init__(self, quibs_allowed: Set, is_within_allowed_quib_get_value: bool = False):
        self._quibs_allowed = quibs_allowed
        self._is_within_allowed_quib_get_value = is_within_allowed_quib_get_value

    def __enter__(self):
        QUIB_GUARDS.append(self)
        return self

    @contextlib.contextmanager
    def get_value_context_manager(self, quib):
        all_allowed_quibs = set().union(*[{quib, *quib._get_children_recursively()} for quib in self._quibs_allowed])
        if self._is_within_allowed_quib_get_value or quib not in all_allowed_quibs:
            raise CannotAccessQuibInScopeException()
        self._is_within_allowed_quib_get_value = True
        yield
        self._is_within_allowed_quib_get_value = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        QUIB_GUARDS.pop()


