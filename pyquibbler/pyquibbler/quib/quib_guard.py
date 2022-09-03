from __future__ import annotations

from dataclasses import dataclass
from typing import Set

from pyquibbler.exceptions import PyQuibblerException

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib


@dataclass
class CannotAccessQuibInScopeException(PyQuibblerException):
    quib: Quib

    def __str__(self):
        return f"Illegal access to {self.quib}. Note that access to quibs from the global scope is not allowed"


class QuibGuard:
    """
    A quib guard allows us to specify places in which only certain quibs (and their recursive children)
    are allowed to be accessed
    """
    _QUIB_GUARDS = []

    def __init__(self, quibs_allowed: Set):
        self._quibs_allowed = set(quibs_allowed)
        for quib in quibs_allowed:
            self._quibs_allowed.update(quib.get_ancestors())

    def __enter__(self):
        self._QUIB_GUARDS.append(self)
        return self

    def raise_if_not_allowed_access_to_quib(self, quib):
        if quib not in self._quibs_allowed:
            raise CannotAccessQuibInScopeException(quib)

    def add_allowed_quib(self, quib: Quib):
        self._quibs_allowed.add(quib)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._QUIB_GUARDS.pop()

    @classmethod
    def is_within_quib_guard(cls):
        return len(cls._QUIB_GUARDS) > 0

    @classmethod
    def get_current_quib_guard(cls) -> QuibGuard:
        return cls._QUIB_GUARDS[-1]


def add_new_quib_to_guard_if_exists(quib: Quib):
    if QuibGuard.is_within_quib_guard():
        QuibGuard.get_current_quib_guard().add_allowed_quib(quib)


def guard_raise_if_not_allowed_access_to_quib(quib: Quib):
    if QuibGuard.is_within_quib_guard():
        QuibGuard.get_current_quib_guard().raise_if_not_allowed_access_to_quib(quib)
