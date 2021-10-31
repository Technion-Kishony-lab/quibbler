import contextlib
from functools import reduce
from typing import Set, Optional

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.quib import Quib

QUIB_GUARD = None


class CannotAccessQuibInScopeException(PyQuibblerException):

    def __str__(self):
        return "You cannot access quibs from the global scope within a user function"


class AnotherQuibGuardIsAlreadyActiveException(PyQuibblerException):
    def __str__(self):
        return "There cannot be two quib guards at once"


class QuibGuard:

    @classmethod
    def create(cls, quibs_allowed: Set[Quib]):
        if QUIB_GUARD is not None:
            raise AnotherQuibGuardIsAlreadyActiveException()
        return cls(quibs_allowed)

    def __init__(self, quibs_allowed: Set):
        self._quibs_allowed = quibs_allowed

    def __enter__(self):
        global QUIB_GUARD
        QUIB_GUARD = self
        return self

    def raise_if_accessing_global_quib(self, quib: Quib):
        all_allowed_quibs = set().union(*[{quib, *quib._get_children_recursively()} for quib in self._quibs_allowed])
        if quib not in all_allowed_quibs:
            raise CannotAccessQuibInScopeException()

    def __exit__(self, exc_type, exc_val, exc_tb):
        global QUIB_GUARD
        QUIB_GUARD = None


