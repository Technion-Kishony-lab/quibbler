import numpy as np

from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.function_definitions.func_call import FuncCall


def get_data_source_mask(func_call: FuncCall, source: Source, indices: np.ndarray) -> np.ndarray:
    """
    Runs the function with True at the source position
    """

    def replace_source_with_bool(obj):
        res = np.full(np.shape(obj.value), False)
        if obj is source:
            res[indices] = True
        return res

    args, kwargs = func_call.transform_sources_in_args_kwargs(transform_data_source_func=replace_source_with_bool)
    return SourceFuncCall.from_(func_call.func, args, kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()
