import pathlib
from dataclasses import dataclass
from typing import Any, Optional, Union

from pyquibbler.assignment import AssignmentTemplate
from pyquibbler.env import DEBUG
from pyquibbler.exceptions import DebugException
from pyquibbler.file_syncing import SaveFormat
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_func_definition
from pyquibbler.path.path_component import Path, Paths
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.func_calling.cache_mode import CacheMode
from pyquibbler.quib.utils.miscellaneous import is_there_a_quib_in_object


from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.translation.types import Source


@dataclass
class CannotNestQuibInIQuibException(DebugException):
    value: Any

    def __str__(self):
        return 'Cannot create an input quib that contains another quib'


def identity_function(v):
    return v


# We do this for the functional_representation to look correct
identity_function.__name__ = 'iquib'


class IQuibForwardsPathTranslator(ForwardsPathTranslator):

    SHOULD_ATTEMPT_WITHOUT_SHAPE_AND_TYPE = True

    def _forward_translate_source(self, source: Source, path: Path) -> Paths:
        return [path]


iquib_definition = create_func_definition(raw_data_source_arguments=[0],
                                          forwards_path_translators=[IQuibForwardsPathTranslator])


def iquib(value: Any,
          cache_mode: CacheMode = None,
          lazy: bool = False,
          allow_overriding: bool = True,
          save_format: Union[None, str, SaveFormat] = None,
          save_directory: Union[None, str, pathlib.Path] = None,
          assigned_name: Optional[str] = None,
          assignment_template: Union[None, tuple, AssignmentTemplate] = None,
          ):
    """
    Returns an input-quib that represent a given object

    Parameters
    ----------
    value : Any
    The value returned by the quib.

    Returns
    -------
    Quib

    See Also
    --------
    q, q_eager, Quib.get_value()
    """

    # iquib is implemented as a quib with an identity function
    if DEBUG:
        if is_there_a_quib_in_object(value, force_recursive=True):
            raise CannotNestQuibInIQuibException(value)

    return create_quib(
        func=identity_function,
        args=(value,),
        assigned_name=assigned_name,
        allow_overriding=allow_overriding,
        assignment_template=assignment_template,
        lazy=lazy,
        save_format=save_format,
        save_directory=save_directory,
        cache_mode=cache_mode,
    )

add_definition_for_function(func=identity_function, function_definition=iquib_definition,
                            quib_creating_func=iquib)
