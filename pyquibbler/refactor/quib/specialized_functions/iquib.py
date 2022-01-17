from dataclasses import dataclass
from typing import Any, List

from pyquibbler.refactor.env import DEBUG
from pyquibbler.refactor.exceptions import DebugException
from pyquibbler.refactor.function_definitions import add_definition_for_function
from pyquibbler.refactor.function_definitions.function_definition import create_function_definition
from pyquibbler.refactor.path.path_component import Path
from pyquibbler.refactor.project import Project
from pyquibbler.refactor.quib.factory import create_quib
from pyquibbler.refactor.quib.function_running.cache_behavior import CacheBehavior
from pyquibbler.refactor.quib.utils.miscellaneous import is_there_a_quib_in_object
from pyquibbler.refactor.quib.quib import Quib


# TODO: should iquib simply be a function that is overridden? How would we handle all flags etc?
from pyquibbler.refactor.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.refactor.translation.types import Source


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
    # TODO: add docs
    if DEBUG:
        if is_there_a_quib_in_object(value, force_recursive=True):
            raise CannotNestQuibInIQuibException(value)

    return create_quib(
        func=identity_function,
        args=(value,),
        allow_overriding=True,
        evaluate_now=True,
        cache_behavior=CacheBehavior.ON,
        can_save_as_txt=True,
        save_directory=Project.get_or_create().input_quib_directory
    )


class IQuibForwardsPathTranslator(ForwardsPathTranslator):
    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        return [path]


iquib_definition = create_function_definition(
    forwards_path_translators=[IQuibForwardsPathTranslator],
    data_source_arguments=[0],
)

add_definition_for_function(func=identity_function, function_definition=iquib_definition)
