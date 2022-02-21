from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING, Callable, Dict, Set, Any

from pyquibbler.exceptions import PyQuibblerException, DebugException
from pyquibbler.quib.func_calling.cache_behavior import CacheBehavior

if TYPE_CHECKING:
    from pyquibbler.quib.quib import Quib
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


@dataclass
class NestedQuibException(DebugException):
    obj: Any
    nested_quibs: Set[Quib]

    def __str__(self):
        return 'PyQuibbler does not support calling functions with arguments that contain deeply nested quibs.\n' \
               f'The quibs {self.nested_quibs} are deeply nested within {self.obj}.'


@dataclass
class FuncCalledWithNestedQuibException(PyQuibblerException):
    func: Callable
    nested_quibs_by_arg_names: Dict[str, Set[Quib]]

    def __str__(self):
        return f'The function {self.func} was called with nested Quib objects. This is not supported.\n' + \
               '\n'.join(f'The argument "{arg}" contains the quibs: {quibs}'
                         for arg, quibs in self.nested_quibs_by_arg_names.items())


@dataclass
class CannotSaveAsTextException(PyQuibblerException):

    def __str__(self):
        return 'The quib assignments contain objects that cannot be saved as text.' \
               'To save the quib set the save_format to "binary".'
