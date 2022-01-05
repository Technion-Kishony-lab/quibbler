from typing import Optional, Tuple, Type, Callable

from pyquibbler.env import GET_VARIABLE_NAMES, SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.logger import logger
from pyquibbler.refactor.func_call import FuncCall
from pyquibbler.refactor.quib.function_runners import FunctionRunner, DefaultFunctionRunner
from pyquibbler.refactor.overriding import get_definition_for_function, CannotFindDefinitionForFunctionException
from pyquibbler.refactor.quib.iterators import iter_quibs_in_args
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.quib.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.refactor.quib.variable_metadata import get_var_name_being_set_outside_of_pyquibbler, \
    get_file_name_and_line_number_of_quib


def get_original_func(func: Callable):
    """
    Get the original func- if this function is already overrided, get the original func it's overriding.

    So for example, if the OVERLOADED np.array is given as `func`, then the ORIGINAL np.array will be returned
    If the ORIGINAL np.array is given as `func`, then `func` will be returned
    """
    if hasattr(func, '__quibbler_wrapped__'):
        return func.__quibbler_wrapped__
    return func


def get_deep_copied_args_and_kwargs(args, kwargs):
    if kwargs is None:
        kwargs = {}
    kwargs = {k: deep_copy_without_quibs_or_graphics(v) for k, v in kwargs.items()}
    args = deep_copy_without_quibs_or_graphics(args)
    return args, kwargs


def get_quib_name() -> Optional[str]:
    should_get_variable_names = GET_VARIABLE_NAMES and not Quib._IS_WITHIN_GET_VALUE_CONTEXT

    try:
        return get_var_name_being_set_outside_of_pyquibbler() if should_get_variable_names else None
    except Exception as e:
        logger.warning(f"Failed to get name, exception {e}")

    return None


def get_file_name_and_line_no() -> Tuple[Optional[str], Optional[str]]:
    should_get_file_name_and_line = SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS and not Quib._IS_WITHIN_GET_VALUE_CONTEXT

    try:
        return get_file_name_and_line_number_of_quib() if should_get_file_name_and_line else None, None
    except Exception as e:
        logger.warning(f"Failed to get file name + lineno, exception {e}")

    return None, None


def create_quib(func, args=(), kwargs=None, cache_behavior=None, evaluate_now=False, is_known_graphics_func=False,
                allow_overriding=False, call_func_with_quibs: bool = False, is_random_func: bool = False,
                **init_kwargs):
    """
    Public constructor for creating a quib.
    # TODO: serious docs
    """

    kwargs = kwargs or {}

    # TODO: how are we handling this situation overall
    call_func_with_quibs = kwargs.pop('call_func_with_quibs', call_func_with_quibs)

    args, kwargs = get_deep_copied_args_and_kwargs(args, kwargs)
    file_name, line_no = get_file_name_and_line_no()
    func = get_original_func(func)

    try:
        definition = get_definition_for_function(func)
    except CannotFindDefinitionForFunctionException:
        function_runner_cls = DefaultFunctionRunner
    else:
        function_runner_cls: Type[FunctionRunner] = definition.function_runner_cls

    runner = function_runner_cls.from_(
        func_call=FuncCall.from_function_call(
            func=func,
            args=args,
            kwargs=kwargs,
            include_defaults=True
        ),
        call_func_with_quibs=call_func_with_quibs,
        graphics_collections=None,
        is_known_graphics_func=is_known_graphics_func,
        is_random_func=is_random_func,
        default_cache_behavior=cache_behavior or FunctionRunner.DEFAULT_CACHE_BEHAVIOR,
        evaluate_now=evaluate_now
    )

    quib = Quib(function_runner=runner,
                assignment_template=None,
                allow_overriding=allow_overriding,
                name=get_quib_name(),
                file_name=file_name,
                line_no=line_no,
                **init_kwargs)

    for arg in iter_quibs_in_args(args, kwargs):
        arg.add_child(quib)

    return quib
