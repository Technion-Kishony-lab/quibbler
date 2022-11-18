import pathlib
from dataclasses import dataclass
from typing import Any, Optional, Union

from pyquibbler.assignment import AssignmentTemplate
from pyquibbler.function_overriding.is_initiated import warn_if_quibbler_not_initiated
from pyquibbler.utilities.decorators import assign_func_name
from pyquibbler.utilities.missing_value import missing
from pyquibbler.env import DEBUG
from pyquibbler.exceptions import DebugException
from pyquibbler.file_syncing import SaveFormat
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.function_definitions.func_definition import create_or_reuse_func_definition
from pyquibbler.quib.factory import create_quib
from pyquibbler.quib.utils.miscellaneous import is_there_a_quib_in_object
from pyquibbler.quib.func_calling.iquib_call import IQuibFuncCall

from pyquibbler.quib.quib import Quib


@dataclass
class CannotNestQuibInIQuibException(DebugException):
    value: Any

    def __str__(self):
        return 'Cannot create an input quib that contains another quib.'


@assign_func_name('iquib')  # For the pretty functional_representation
def identity_function(v):
    return v


iquib_definition = create_or_reuse_func_definition(raw_data_source_arguments=[0], is_random=False, is_graphics=False,
                                                   lazy=False, forwards_path_translators=[],
                                                   quib_function_call_cls=IQuibFuncCall)


def iquib(value: Any,
          allow_overriding: bool = True,
          save_format: Union[None, str, SaveFormat] = None,
          save_directory: Union[None, str, pathlib.Path] = None,
          assigned_name: Optional[str] = missing,
          assignment_template: Union[None, tuple, AssignmentTemplate] = None,
          ) -> Quib:
    """
    Returns an input-quib that represents a given object

    Parameters
    ----------
    value : Any
        The value returned by the quib.

    allow_overriding : bool, default True
        Whether to allow overriding assignments to the quib.

    save_format : {None, 'off', 'txt', 'bin'} or SaveFormat
        The format in which quib assignments are saved to file.
        default: None

    save_directory: None, str, pathlib.Path
        The directory in which quib assignments are to be saved.
        default: None

    assigned_name: None, str
        A name assigned to the quib. If assigned_name is not specified, the name is assigned based on the name of the
        variable to which the quib is assigned.
        default: None

    assignment_template: None, tuple, AssignmentTemplate
        A template to restrict quib assignments
        default: None

    Returns
    -------
    Quib

    See Also
    --------
    q, quiby, Quib.get_value
    Quib.allow_overriding, Quib.save_format, Quib.save_directory, Quib.assigned_name, Quib.assignment_template
    """

    warn_if_quibbler_not_initiated()

    if DEBUG:
        if is_there_a_quib_in_object(value, recursive=True):
            raise CannotNestQuibInIQuibException(value)

    # iquib is implemented as a quib with an identity function
    return create_quib(
        func=identity_function,
        args=(value,),
        assigned_name=assigned_name,
        allow_overriding=allow_overriding,
        assignment_template=assignment_template,
        save_format=save_format,
        save_directory=save_directory,
    )


add_definition_for_function(func=identity_function,
                            func_definition=iquib_definition,
                            quib_creating_func=iquib)
