from __future__ import annotations
import pathlib
from typing import Optional, Callable, Union, Set, List

from pyquibbler.assignment import AssignmentTemplate
from pyquibbler.utilities.missing_value import missing
from pyquibbler.utilities.general_utils import Kwargs, Args
from pyquibbler.env import LAZY, GRAPHICS_LAZY
from pyquibbler.project import Project
from pyquibbler.file_syncing.types import SaveFormat
from pyquibbler.function_definitions.func_definition import FuncDefinition
from pyquibbler.function_definitions import get_definition_for_function, SourceLocation
from pyquibbler.utilities.get_original_func import get_original_func
from .func_calling.cached_quib_func_call import CachedQuibFuncCall
from .graphics import GraphicsUpdateType
from .quib_guard import add_new_quib_to_guard_if_exists
from .quib import Quib
from .utils.miscellaneous import deep_copy_without_quibs_or_graphics
from .variable_metadata import get_file_name_and_line_no, get_quib_name

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyquibbler import CacheMode


def create_quib(func: Optional[Callable],
                args: Args = (),
                kwargs: Kwargs = None,
                func_definition: FuncDefinition = None,
                cache_mode: CacheMode = None,
                lazy: bool = missing,
                allow_overriding: bool = False,
                graphics_update: GraphicsUpdateType = None,
                save_format: Optional[SaveFormat] = None,
                save_directory: pathlib.Path = None,
                assigned_name: Optional[str] = missing,
                assignment_template: Union[None, tuple, AssignmentTemplate] = None,
                assigned_quibs: Optional[Set[Quib]] = None,
                register_as_child_of_parents: bool = True,
                quib_locations: List[SourceLocation] = None,
                ) -> Quib:
    """
    Public constructor for creating a quib
    Takes care of retrieving all relevant info for the creation of the
    quib as well as registering and performing any calculations.

    Returns a Quib object.
    """

    kwargs = kwargs or {}

    if func is None:
        func = func_definition.func
    else:
        func_definition = func_definition or get_definition_for_function(func)

    cache_mode = cache_mode or CachedQuibFuncCall.DEFAULT_CACHE_MODE
    assigned_name = get_quib_name() if assigned_name is missing else assigned_name

    quib = Quib(created_in=get_file_name_and_line_no(),
                func=get_original_func(func),
                args=deep_copy_without_quibs_or_graphics(args),
                kwargs=deep_copy_without_quibs_or_graphics(kwargs),
                func_definition=func_definition,
                )

    quib.setp(assignment_template=assignment_template,
              assigned_quibs=assigned_quibs,
              allow_overriding=allow_overriding,
              assigned_name=assigned_name,
              graphics_update=graphics_update,
              save_directory=save_directory,
              save_format=save_format,
              cache_mode=cache_mode,
              )

    quib.handler.reset_quib_func_call()
    quib.handler.quib_function_call.load_source_locations(quib_locations)

    # register new quib on project
    project = Project.get_or_create()
    project.register_quib(quib)

    add_new_quib_to_guard_if_exists(quib)

    # register new quib on parents
    if register_as_child_of_parents:
        quib.handler.connect_to_parents()

    # evaluate now if not lazy
    lazy = func_definition.lazy if lazy is missing else lazy
    if lazy is None:
        lazy = GRAPHICS_LAZY if func_definition.is_graphics else LAZY
    if not lazy:
        quib.get_value()

    return quib
