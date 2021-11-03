from __future__ import annotations
import contextlib
from dataclasses import dataclass
from typing import Set, TYPE_CHECKING

from pyquibbler.exceptions import PyQuibblerException

if TYPE_CHECKING:
    from pyquibbler.quib import Quib

QUIB_GUARDS = []


def is_within_quib_guard():
    return len(QUIB_GUARDS) > 0


def get_current_quib_guard():
    return QUIB_GUARDS[-1]


@dataclass
class CannotAccessQuibInScopeException(PyQuibblerException):
    quib: Quib

    def __str__(self):
        return f"Illegal access to {self.quib}. Note that access to quibs from the global scope is not allowed"


class AnotherQuibGuardIsAlreadyActiveException(PyQuibblerException):
    def __str__(self):
        return "There cannot be two quib guards at once"


class QuibGuard:
    """
    A quib guard allows you to specify places in which only certain quibs (and their recursive children)
    are allowed to be accessed
    """

    def __init__(self, quibs_allowed: Set, allowed_quib_get_values_count: int = 0):
        self._quibs_allowed = quibs_allowed
        self._allowed_quib_get_values_count = allowed_quib_get_values_count

    def __enter__(self):
        QUIB_GUARDS.append(self)
        return self

    @contextlib.contextmanager
    def get_value_context_manager(self, quib):
        all_allowed_quibs = set().union(*[{quib, *quib._get_children_recursively()} for quib in self._quibs_allowed])
        if self._allowed_quib_get_values_count == 0 and quib not in all_allowed_quibs:
            raise CannotAccessQuibInScopeException(quib)
        self._allowed_quib_get_values_count += 1
        yield
        self._allowed_quib_get_values_count -= 1

    def __exit__(self, exc_type, exc_val, exc_tb):
        QUIB_GUARDS.pop()
