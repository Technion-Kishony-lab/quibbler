from __future__ import annotations
import pathlib
from typing import Optional, Tuple, Callable, Any, Mapping, TYPE_CHECKING

from pyquibbler.env import GET_VARIABLE_NAMES, SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.logger import logger
from pyquibbler.project import Project
from pyquibbler.quib.func_calling import QuibFuncCall
from pyquibbler.function_definitions import get_definition_for_function
from pyquibbler.quib.get_value_context_manager import is_within_get_value_context
from pyquibbler.quib.graphics import UpdateType
from pyquibbler.quib.quib_guard import add_new_quib_to_guard_if_exists
from pyquibbler.quib.quib import Quib
from pyquibbler.quib.types import FileAndLineNumber
from pyquibbler.quib.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.quib.variable_metadata import get_var_name_being_set_outside_of_pyquibbler, \
    get_file_name_and_line_number_of_quib
from pyquibbler.file_syncing.types import SaveFormat

if TYPE_CHECKING:
    from pyquibbler import CacheBehavior


def get_original_func(func: Callable):
    """
    Get the original func- if this function is already overrided, get the original func it's function_definitions.

    So for example, if the OVERLOADED np.array is given as `func`, then the ORIGINAL np.array will be returned
    If the ORIGINAL np.array is given as `func`, then `func` will be returned
    """
    while hasattr(func, '__quibbler_wrapped__'):
        func = func.__quibbler_wrapped__
    return func


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


def _get_deep_copied_args_and_kwargs(args, kwargs):
    """
    Get deep copied args and kwargs- any manipulation of the returned values should not affect the parameter values.
    """
    if kwargs is None:
        kwargs = {}
    kwargs = {k: deep_copy_without_quibs_or_graphics(v) for k, v in kwargs.items()}
    args = deep_copy_without_quibs_or_graphics(args)
    return args, kwargs


def create_quib(func: Callable, args: Tuple[Any, ...] = (), kwargs: Mapping[str, Any] = None,
                cache_behavior: CacheBehavior = None,
                evaluate_now: bool = False,
                allow_overriding: bool = False,
                call_func_with_quibs: bool = False,
                update_type: UpdateType = None,
                save_format: Optional[SaveFormat] = None,
                save_directory: pathlib.Path = None,
                **init_kwargs):
    """
    Public constructor for creating a quib- this takes care of retrieving all relevant info for the creation of the
    quib as well as registering and performing any calculations.
    Returns a Quib object.

    :param func - The function this quib represents
    :param args - Positional arguments of the quib's function
    :param kwargs - Keyword arguments of the quib's function
    :param cache_behavior - In what fashion should the quib cache? See CacheBehavior for options
    :param evaluate_now - by default we are lazy- should the quib be evaluated immediately upon creation?
    :param allow_overriding - can this quib be overridden, or does it always need to propogate assignments backwards?
    :param call_func_with_quibs - by default, any quibs in the args will be translated to their values before being the
    quib's function is run. If `call_func_with_quibs` is True, quibs will NOT be translated to their values, and the
    func will be called with the quibs.
    :param update_type - (Only relevant if the quib has graphics/is known graphics func) - when should the quib
    "update"? See UpdateType for options
    :param save_format - indicating the file format for saving assignments to the quib (FileFormat).
    :param save_directory - where to save the quib?
    """

    kwargs = kwargs or {}

    # We have the possiblility of certain Quib parameters to be in the kwargs of the specific call.
    # We may want to move this out per function- for now, we have generic handling for all funcs with
    # `call_func_with_quibs`
    call_func_with_quibs = kwargs.pop('call_func_with_quibs', call_func_with_quibs)

    args, kwargs = _get_deep_copied_args_and_kwargs(args, kwargs)
    created_in = _get_file_name_and_line_no()
    func = get_original_func(func)

    definition = get_definition_for_function(func)
    project = Project.get_or_create()

    quib_func_call = definition.quib_function_call_cls.from_(
        func=func,
        func_args=args,
        func_kwargs=kwargs,
        call_func_with_quibs=call_func_with_quibs,
        default_cache_behavior=cache_behavior or QuibFuncCall.DEFAULT_CACHE_BEHAVIOR,
        include_defaults=True,
    )

    quib = Quib(quib_function_call=quib_func_call, created_in=created_in)

    quib.setp(assignment_template=None, allow_overriding=allow_overriding,
              assigned_name=get_quib_name(), graphics_update_type=None, can_contain_graphics=update_type is not None,
              save_directory=save_directory, save_format=save_format)

    quib.func = func
    quib.args = args
    quib.kwargs = kwargs
    quib.call_func_with_quibs = call_func_with_quibs
    quib.default_cache_behavior = cache_behavior or QuibFuncCall.DEFAULT_CACHE_BEHAVIOR

    project.register_quib(quib)
    add_new_quib_to_guard_if_exists(quib)

    if update_type:
        quib.graphics_update_type = update_type or UpdateType.DRAG

    for arg in quib.parents:
        arg.handler.add_child(quib)

    if evaluate_now:
        quib.get_value()

    return quib
