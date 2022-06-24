import numpy as np
from typing import Dict

from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.function_definitions.func_call import FuncCall


def get_data_source_ids_mask(func_call: FuncCall, sources_to_indices: Dict[Source, np.ndarray] = None) -> np.ndarray:
    """
    Runs the function with each source's id instead of it's values
    """

    sources_to_indices = sources_to_indices or {}

    def replace_source_with_id(obj):
        res = np.full(np.shape(obj.value), 0)
        res[sources_to_indices.get(obj, True)] = id(obj)
        return res

    args, kwargs = func_call.transform_sources_in_args_kwargs(transform_data_source_func=replace_source_with_id)
    return SourceFuncCall.from_(func=func_call.func,
                                func_args=args,
                                func_kwargs=kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()
