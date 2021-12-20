from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pyquibbler.exceptions import PyQuibblerException
from pyquibbler.refactor.quib.cache_behavior import CacheBehavior

if TYPE_CHECKING:
    from pyquibbler.refactor.quib.quib import Quib
    from pyquibbler import Assignment


@dataclass
class OverridingNotAllowedException(PyQuibblerException):
    quib: Quib
    override: Assignment

    def __str__(self):
        return f'Cannot override {self.quib} with {self.override} as it does not allow overriding.'


@dataclass
class UnknownUpdateTypeException(PyQuibblerException):
    attempted_update_type: str

    def __str__(self):
        return f"{self.attempted_update_type} is not a valid update type"


@dataclass
class InvalidCacheBehaviorForQuibException(PyQuibblerException):
    invalid_cache_behavior: CacheBehavior

    def __str__(self):
        return 'This quib must always cache function results, ' \
               'so they are not changed until they are refreshed. ' \
               f'Therefore, the cache behavior should be always set to {CacheBehavior.ON}, ' \
               f'and {self.invalid_cache_behavior} is invalid.'
