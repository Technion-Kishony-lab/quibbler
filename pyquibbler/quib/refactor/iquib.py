from dataclasses import dataclass
from typing import Any

from pyquibbler.env import DEBUG
from pyquibbler.exceptions import DebugException
from pyquibbler.quib.refactor.cache_behavior import CacheBehavior
from pyquibbler.quib.refactor.factory import create_quib

from pyquibbler.quib.refactor.quib import Quib


# TODO: should iquib simply be a function that is overridden? How would we handle all flags etc?
from pyquibbler.quib.utils import is_there_a_quib_in_object


@dataclass
class CannotNestQuibInIQuibException(DebugException):
    iquib: Quib

    def __str__(self):
        return 'Cannot create an input quib that contains another quib'


def identity_function(v):
    return v


# We do this for the functional_representation to look correct
identity_function.__name__ = 'iquib'


def iquib(value: Any):
    if DEBUG:
        if is_there_a_quib_in_object(value, force_recursive=True):
            raise CannotNestQuibInIQuibException(value)

    return create_quib(
        func=identity_function,
        args=(value,),
        allow_overriding=True,
        evaluate_now=True,
        cache_behavior=CacheBehavior.ON
    )
