import numpy as np
from typing import Callable, Set, Dict

from pyquibbler.refactor.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.refactor.translation.types import Source
from pyquibbler.refactor.translation.utils import call_func_with_sources_values
from pyquibbler.refactor.function_definitions.func_call import FuncCall
from pyquibbler.refactor.quib.iterators import recursively_run_func_on_object, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH
from pyquibbler.utils import convert_args_and_kwargs


def get_data_sources(func_call: FuncCall) -> Set[Source]:
    return set(iter_objects_of_type_in_object_shallowly(Source, func_call.get_data_source_argument_values()))


def _convert_data_sources_in_args(func_call: FuncCall, convert_data_source: Callable):
    """
    Return self.args and self.kwargs with all data source args converted with the given convert_data_source
    callback.
    """

    def _convert_arg(_i, arg):
        def _convert_object(o):
            if isinstance(o, Source):
                if o in get_data_sources(func_call):
                    return convert_data_source(o)
                return o.value
            return o

        return recursively_run_func_on_object(func=_convert_object,
                                              obj=arg,
                                              max_depth=SHALLOW_MAX_DEPTH,
                                              max_length=SHALLOW_MAX_LENGTH)

    return convert_args_and_kwargs(_convert_arg,
                                   func_call.args_values.args,
                                   func_call.args_values.kwargs)


def get_data_source_ids_mask(func_call, sources_to_indices: Dict[Source, np.ndarray] = None) -> np.ndarray:
    """
    Runs the function with each quib's ids instead of it's values
    """

    sources_to_indices = sources_to_indices or {}

    def replace_source_with_id(obj):
        if isinstance(obj, Source):
            res = np.full(np.shape(obj.value), 0)
            res[sources_to_indices.get(obj, True)] = id(obj)
            return res
        return obj

    args, kwargs = _convert_data_sources_in_args(func_call, replace_source_with_id)
    return call_func_with_sources_values(func_call.func, args, kwargs)
