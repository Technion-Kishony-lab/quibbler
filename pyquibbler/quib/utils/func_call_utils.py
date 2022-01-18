import functools
from typing import Optional, Dict, Union, Any

from pyquibbler.path.path_component import Path
from pyquibbler.quib.quib_ref import QuibRef
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_shallowly, recursively_run_func_on_object
from pyquibbler.quib.quib import Quib


def get_args_and_kwargs_valid_at_quibs_to_paths(func_call: FuncCall, quibs_to_valid_paths: Dict[Quib, Optional[Path]]):
    """
    Prepare arguments to call self.func with - replace quibs with values valid at the given path,
    and QuibRefs with quibs.
    """

    quibs_allowed_to_access = set()

    def _replace_sub_argument_with_value(func_call: FuncCall, quibs_to_paths, inner_arg: Union[Quib, Any]):
        """
        Replace an argument, potentially a quib, with it's relevant value, given a map of quibs_to_paths, which
        describes for each quib what path it needs to be valid at
        """
        if isinstance(inner_arg, QuibRef):
            res = inner_arg.quib
            quibs_allowed_to_access.add(res)
            return res

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

    replace_func = functools.partial(_replace_sub_argument_with_value, func_call, quibs_to_valid_paths)
    new_args = [recursively_run_func_on_object(replace_func, arg) for arg in func_call.args]
    new_kwargs = {key: recursively_run_func_on_object(replace_func, val) for key, val in func_call.kwargs.items()}
    return new_args, new_kwargs, quibs_allowed_to_access


def is_quib_a_data_source(func_call: FuncCall, quib: Quib):
    return quib in get_data_source_quibs(func_call)


def get_data_source_quibs(func_call: FuncCall):
    return set(iter_objects_of_type_in_object_shallowly(Quib,  func_call.get_data_source_argument_values()))
