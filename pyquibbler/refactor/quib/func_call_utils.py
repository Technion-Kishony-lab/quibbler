import functools
from typing import Optional, Dict, Union, Any

from pyquibbler.refactor.quib.assignment import Path
from pyquibbler.quib.utils import QuibRef
from pyquibbler.refactor.func_call import FuncCall
from pyquibbler.refactor.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.refactor.quib.iterators import recursively_run_func_on_object
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.translation.types import Source


def _replace_sub_argument_with_value(func_call: FuncCall, quibs_to_paths, inner_arg: Union[Quib, Any]):
    """
    Replace an argument, potentially a quib, with it's relevant value, given a map of quibs_to_paths, which
    describes for each quib what path it needs to be valid at
    """
    if isinstance(inner_arg, QuibRef):
        return inner_arg.quib

    if isinstance(inner_arg, Quib):
        if inner_arg in quibs_to_paths:
            path = quibs_to_paths[inner_arg]
        elif is_quib_a_data_source(func_call, inner_arg):
            # If the quib is a data source, and we didn't see it in the result, we don't need it to be valid at any
            # paths (it did not appear in quibs_to_paths)
            path = None
        else:
            # This is a paramater quib- we always need a parameter quib to be completely valid regardless of where
            # we need ourselves (this quib) to be valid
            path = []

        return inner_arg.get_value_valid_at_path(path)

    return inner_arg


def get_func_call_with_quibs_valid_at_paths(func_call: FuncCall, quibs_to_valid_paths: Dict[Quib, Optional[Path]]):
    """
    Prepare arguments to call self.func with - replace quibs with values valid at the given path,
    and QuibRefs with quibs.
    """
    replace_func = functools.partial(_replace_sub_argument_with_value, func_call, quibs_to_valid_paths)
    new_args = [recursively_run_func_on_object(replace_func, arg) for arg in func_call.args]
    new_kwargs = {key: recursively_run_func_on_object(replace_func, val) for key, val in func_call.kwargs.items()}
    return FuncCall.from_function_call(func_call.func,
                                       args=tuple(new_args),
                                       kwargs=new_kwargs,
                                       include_defaults=False)


def is_quib_a_data_source(func_call: FuncCall, quib: Quib):
    return quib in get_data_source_quibs(func_call)


def get_data_source_quibs(func_call: FuncCall):
    return set(iter_objects_of_type_in_object_shallowly(Quib,  func_call.get_data_source_argument_values()))
