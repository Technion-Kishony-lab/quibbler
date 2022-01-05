from copy import copy
from typing import Any, Optional, Tuple, Mapping, Callable, Dict

from pyquibbler.env import DEBUG
from pyquibbler.refactor.iterators import is_iterator_empty, iter_args_and_names_in_function_call, SHALLOW_MAX_LENGTH, \
    SHALLOW_MAX_DEPTH, recursively_run_func_on_object
from pyquibbler.refactor.quib.iterators import iter_quibs_in_object, iter_quibs_in_args, \
    iter_quibs_in_object_recursively


def is_there_a_quib_in_object(obj, force_recursive: bool = False):
    """
    Returns true if there is a quib object nested inside the given object and false otherwise.
    """
    return not is_iterator_empty(iter_quibs_in_object(obj, force_recursive))


def is_there_a_quib_in_args(args, kwargs):
    """
    Returns true if there is a quib object nested inside the given args and kwargs and false otherwise.
    For use by function wrappers that need to determine if the underlying function was called with a quib.
    """
    return not is_iterator_empty(iter_quibs_in_args(args, kwargs))


def deep_copy_without_quibs_or_graphics(obj: Any, max_depth: Optional[int] = None, max_length: Optional[int] = None):
    from matplotlib.artist import Artist

    def copy_if_not_quib_or_artist(o):
        from matplotlib.widgets import AxesWidget
        from pyquibbler.refactor.quib.quib import Quib
        if isinstance(o, (Quib, Artist, AxesWidget)):
            return o
        return copy(o)

    return recursively_run_func_on_object(func=copy_if_not_quib_or_artist, max_length=max_length,
                                          max_depth=max_depth, obj=obj)


def get_nested_quibs_by_arg_names_in_function_call(func: Callable, args: Tuple[Any, ...], kwargs: Dict[str, Any]):
    """
    Look for erroneously nested quibs in a function call and return a mapping between arg names and the quibs they
    have nested inside them.
    """
    nested_quibs_by_arg_names = {}
    for name, val in iter_args_and_names_in_function_call(func, args, kwargs, False):
        quibs = set(iter_quibs_in_object_recursively(val))
        if quibs:
            nested_quibs_by_arg_names[name] = quibs
    return nested_quibs_by_arg_names


def copy_and_replace_quibs_with_vals(obj: Any):
    """
    Copy `obj` while replacing quibs with their values, with a limited depth and length.
    """
    from pyquibbler.refactor.quib.quib import Quib
    from matplotlib.artist import Artist

    def replace_with_value_if_quib_or_copy(o):
        # if isinstance(o, QuibRef):
        #     return o.quib
        if isinstance(o, Quib):
            return o.get_value()
        if isinstance(o, Artist):
            return o
        try:
            return copy(o)
        except NotImplementedError:
            return o

    result = recursively_run_func_on_object(func=replace_with_value_if_quib_or_copy, max_depth=SHALLOW_MAX_DEPTH,
                                            max_length=SHALLOW_MAX_LENGTH, obj=obj)
    if DEBUG: # and not isinstance(obj, QuibRef):
        nested_quibs = set(iter_quibs_in_object_recursively(result))
        if nested_quibs:
            # TODO: Change to NestedQuibException
            raise Exception(obj, nested_quibs)
    return result


def copy_and_convert_args_and_kwargs_to_values(args: Tuple[Any, ...], kwargs: Mapping[str, Any]):
    """
    Copy and convert args and kwargs to their respective values- if an arg is a quib it will be replaced with a value,
    elsewise it will just be copied
    """
    return (tuple(copy_and_replace_quibs_with_vals(arg) for arg in args),
            {name: copy_and_replace_quibs_with_vals(val) for name, val in kwargs.items()})


def call_func_with_quib_values(func, args, kwargs):
    """
    Calls a function with the specified args and kwargs while replacing quibs with their values.
    """
    new_args, new_kwargs = copy_and_convert_args_and_kwargs_to_values(args, kwargs)
    try:
        return func(*new_args, **new_kwargs)
    except TypeError as e:
        if len(e.args) == 1 and 'Quib' in e.args[0]:
            nested_quibs_by_arg_names = get_nested_quibs_by_arg_names_in_function_call(func, new_args, new_kwargs)
            if nested_quibs_by_arg_names:
                # TODO: FunctionCalledWithNestedQuibException
                raise Exception(func, nested_quibs_by_arg_names) from e
        raise




