import numpy as np

from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.types import Source
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.utilities.iterators import iter_objects_matching_criteria_in_object_recursively


def get_data_source_mask(func_call: FuncCall, source: Source, indices: np.ndarray) -> np.ndarray:
    """
    Runs the function with True at the source position
    """

    def replace_source_with_bool(current_source: Source):
        res = np.full(np.shape(current_source.value), False)
        if current_source is source:
            res[indices] = True
        return res

    args, kwargs = func_call.transform_sources_in_args_kwargs(transform_data_source_func=replace_source_with_bool)
    return SourceFuncCall.from_(func_call.func, args, kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()


OFFSET = 123456789


def get_data_source_indices(func_call: FuncCall, source: Source) -> np.ndarray:
    """
    Runs the function with the source replaced with array of linear indices
    """

    def replace_source_with_indices(current_source: Source):
        shape = np.shape(current_source.value)

        if current_source is source:
            size = np.size(current_source.value)
            return np.arange(OFFSET, OFFSET + size).reshape(shape)
        return np.full(shape, -1)

    args, kwargs = func_call.transform_sources_in_args_kwargs(transform_data_source_func=replace_source_with_indices)
    return SourceFuncCall.from_(func_call.func, args, kwargs,
                                func_definition=func_call.func_definition,
                                data_source_locations=[],
                                parameter_source_locations=func_call.parameter_source_locations).run()


def find_all_indices(obj: np.ndarray):

    def is_non_object_array(sub_obj):
        return isinstance(sub_obj, np.ndarray) and sub_obj.dtype.type is not np.object_ \
               or isinstance(sub_obj, np.int64) and sub_obj >= OFFSET

    arrays = iter_objects_matching_criteria_in_object_recursively(is_non_object_array, obj, prevent_repetitions=False)
    list_of_arrays_of_indices = [[array - OFFSET] if isinstance(array, np.int64)
                                 else array[array >= OFFSET] - OFFSET for array in arrays]

    if list_of_arrays_of_indices:
        return np.concatenate(list_of_arrays_of_indices)

    return np.zeros(0)
