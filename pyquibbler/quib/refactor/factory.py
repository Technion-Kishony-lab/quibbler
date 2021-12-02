import types
from typing import Optional, Tuple

from pyquibbler.env import GET_VARIABLE_NAMES, SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.logger import logger
from pyquibbler.quib.refactor.iterators import iter_quibs_in_args
from pyquibbler.quib.refactor.quib import Quib
from pyquibbler.quib.refactor.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.quib.refactor.variable_metadata import get_var_name_being_set_outside_of_pyquibbler, \
    get_file_name_and_line_number_of_quib


def unwrap_func_if_quib_class(func):
    """
    If we received a function that was already wrapped with a quib class, we want want to unwrap it
    """
    while hasattr(func, '__quib_wrapper__'):
        previous_func = func
        func = func.__wrapped__
        # If it was a bound method we need to recreate it
        if hasattr(previous_func, '__self__'):
            func = types.MethodType(func, previous_func.__self__)
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
                allow_overriding=False, pass_quibs: bool = False,
                **init_kwargs):
    """
    Public constructor for creating a quib.
    """
    args, kwargs = get_deep_copied_args_and_kwargs(args, kwargs)
    file_name, line_no = get_file_name_and_line_no()

    quib = Quib(func=unwrap_func_if_quib_class(func),
                args=args,
                kwargs=kwargs,
                cache_behavior=cache_behavior,
                assignment_template=None,
                allow_overriding=allow_overriding,
                is_known_graphics_func=is_known_graphics_func,
                name=get_quib_name(),
                file_name=file_name,
                line_no=line_no,
                **init_kwargs)

    for arg in iter_quibs_in_args(args, kwargs):
        arg.add_child(quib)

    if evaluate_now:
        quib.get_value()

    return quib
