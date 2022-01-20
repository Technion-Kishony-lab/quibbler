from typing import Callable, Any, Tuple, Mapping

from pyquibbler import Assignment
from pyquibbler.function_definitions import get_definition_for_function
from pyquibbler.function_definitions.func_call import FuncCall, ArgsValues
from pyquibbler.inversion.invert import invert
from pyquibbler.path.data_accessing import deep_assign_data_in_path
from pyquibbler.quib.factory import get_original_func
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.path import PathComponent
from pyquibbler.translation.types import Source
from pyquibbler.utilities.iterators import get_paths_for_objects_of_type


def _get_data_source_locations_and_parameter_locations(func, args, kwargs):
    definition = get_definition_for_function(func)
    args_values = ArgsValues.from_func_args_kwargs(func, args, kwargs, include_defaults=True)
    data_arguments_with_values = definition.get_data_source_arguments_with_values(args_values)
    parameter_arguments_with_values = definition.get_parameter_arguments_with_values(func, args_values)

    data_source_arguments_with_paths = [
        (argument, get_paths_for_objects_of_type(obj=value, type_=Source))
        for argument, value in data_arguments_with_values
    ]

    parameter_source_arguments_with_paths = [
        (argument, get_paths_for_objects_of_type(obj=value, type_=Source))
        for argument, value in parameter_arguments_with_values
    ]

    return data_source_arguments_with_paths, parameter_source_arguments_with_paths


def inverse(func: Callable, indices: Any, value: Any, args: Tuple[Any, ...] = None, kwargs: Mapping[str, Any] = None,
            empty_path: bool = False):
    func = get_original_func(func)
    if indices is not None and empty_path is True:
        raise Exception("The indices cannot be set if empty path is True")

    args = args or tuple()
    kwargs = kwargs or {}
    previous_value = SourceFuncCall.from_(func, args, kwargs).run()
    inversals = invert(
        func_call=SourceFuncCall.from_(
            func=func,
            func_args=args,
            func_kwargs=kwargs,
            include_defaults=False
        ),
        previous_result=previous_value,
        assignment=Assignment(path=[PathComponent(indexed_cls=type(previous_value),
                                                  component=indices)] if not empty_path else [],
                              value=value)
    )

    return {
        inversal.source: deep_assign_data_in_path(inversal.source.value,
                                                  inversal.assignment.path,
                                                  inversal.assignment.value)
        for inversal in inversals
    }