from typing import Any, Callable, Dict

from pyquibbler.translation.types import Source
from pyquibbler.translation.utils import copy_and_replace_sources_with_vals


def call_func_with_sources_values(func: Callable, args, kwargs):
    """
    Calls a function with the specified args and kwargs while replacing quibs with their values.
    """
    new_args = (tuple(copy_and_replace_sources_with_vals(arg) for arg in args))
    new_kwargs = {name: copy_and_replace_sources_with_vals(val) for name, val in kwargs.items()}
    return func(*new_args, **new_kwargs)


def create_inverse_func_from_indexes_to_funcs(data_source_argument_indexes_to_inverse_functions: Dict[int, Callable]):
    """
    Create an inverse function that will call actual inverse functions based on the index of the quib in the arguments
    """

    def _inverse(representative_result: Any, args, kwargs, source_to_change: Source, relevant_path_in_source):
        source_index = next(i for i, v in enumerate(args) if v is source_to_change)
        inverse_func = data_source_argument_indexes_to_inverse_functions[source_index]
        new_args = list(args)
        new_args.pop(source_index)
        return call_func_with_sources_values(func=inverse_func,
                                             args=(representative_result, *new_args),
                                             kwargs=kwargs)

    return _inverse


def create_inverse_single_arg_func(inverse_func: Callable):
    """
    Create an inverse function that will call actual inverse functions for single argument functions
    """

    def _inverse(representative_result: Any, args, kwargs, source_to_change: Source, relevant_path_in_source):
        return call_func_with_sources_values(inverse_func, [representative_result, *args], kwargs)

    return _inverse
