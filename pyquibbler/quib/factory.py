from __future__ import annotations
import pathlib
from typing import Optional, Tuple, Callable, Any, Mapping, TYPE_CHECKING, Union, Set

from pyquibbler.assignment import AssignmentTemplate
from pyquibbler.env import GET_VARIABLE_NAMES, SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.logger import logger
from pyquibbler.project import Project
from pyquibbler.quib.func_calling import CachedQuibFuncCall
from pyquibbler.quib.get_value_context_manager import is_within_get_value_context
from pyquibbler.quib.graphics import GraphicsUpdateType
from pyquibbler.quib.quib_guard import add_new_quib_to_guard_if_exists
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.types import FileAndLineNumber
from pyquibbler.quib.variable_metadata import get_var_name_being_set_outside_of_pyquibbler, \
    get_file_name_and_line_number_of_quib
from pyquibbler.file_syncing.types import SaveFormat
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.function_definitions import get_definition_for_function

if TYPE_CHECKING:
    from pyquibbler import CacheMode


def get_quib_name() -> Optional[str]:
    """
    Get the quib's name- this can potentially return None
    if the context makes getting the file name and line no irrelevant
    """
    if GET_VARIABLE_NAMES and not is_within_get_value_context():
        try:
            return get_var_name_being_set_outside_of_pyquibbler()
        except Exception as e:
            logger.warning(f"Failed to get name, exception {e}")

    return None


def _get_file_name_and_line_no() -> Optional[FileAndLineNumber]:
    """
    Get the file name and line no where the quib was created (outside of pyquibbler)- this can potentially return Nones
    if the context makes getting the file name and line no irrelevant
    """
    if SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS and not is_within_get_value_context():
        try:
            return get_file_name_and_line_number_of_quib()
        except Exception as e:
            logger.warning(f"Failed to get file name + lineno, exception {e}")

    return None


def create_quib(func: Callable,
                args: Tuple[Any, ...] = (),
                kwargs: Mapping[str, Any] = None,
                function_definition: FuncDefinition = None,
                cache_mode: CacheMode = None,
                lazy: bool = None,
                allow_overriding: bool = False,
                graphics_update: GraphicsUpdateType = None,
                save_format: Optional[SaveFormat] = None,
                save_directory: pathlib.Path = None,
                assigned_name: Optional[str] = None,
                assignment_template: Union[None, tuple, AssignmentTemplate] = None,
                assigned_quibs: Optional[Set[Quib]] = None,
                register_as_child_of_parents: bool = True,
                ) -> Quib:
    """
    Public constructor for creating a quib
    Takes care of retrieving all relevant info for the creation of the
    quib as well as registering and performing any calculations.

    Returns a Quib object.
    """

    quib = Quib(created_in=_get_file_name_and_line_no())

    kwargs = kwargs or {}
    function_definition = function_definition or get_definition_for_function(func)
    lazy = function_definition.lazy if lazy is None else lazy
    cache_mode = cache_mode or CachedQuibFuncCall.DEFAULT_CACHE_MODE
    assigned_name = get_quib_name() if assigned_name is None else assigned_name

    quib.setp(assignment_template=assignment_template,
              assigned_quibs=assigned_quibs,
              allow_overriding=allow_overriding,
              assigned_name=assigned_name,
              graphics_update=graphics_update,
              save_directory=save_directory,
              save_format=save_format,
              cache_mode=cache_mode,
              )

    quib.func = func
    quib.args = args
    quib.kwargs = kwargs
    quib.handler.func_definition = function_definition
    quib.handler.reset_quib_func_call()

    # register new quib on project
    project = Project.get_or_create()
    project.register_quib(quib)

    add_new_quib_to_guard_if_exists(quib)

    # register new quib on parents
    if register_as_child_of_parents:
        for parent in quib.parents:
            parent.handler.add_child(quib)

    # evaluate now if not lazy
    if not lazy:
        quib.get_value()

    return quib
