from __future__ import annotations
from typing import TYPE_CHECKING

from pyquibbler.translation.types import Source, NoMetadataSource
from pyquibbler.translation.source_func_call import SourceFuncCall


if TYPE_CHECKING:
    from pyquibbler.quib.func_calling import QuibFuncCall


def get_func_call_for_translation_with_sources_metadata(func_call: QuibFuncCall):
    """
    Get a source func call along with the newly created data sources to the quibs they represent
    All sources will be in correct shape and type
    """
    data_sources_to_quibs = {}

    def _transform_data_quib(quib):
        source = Source(quib.get_value_valid_at_path(None))
        data_sources_to_quibs[source] = quib
        return source

    def _transform_parameter_quib(quib):
        return Source(quib.get_value_valid_at_path([]))

    new_args, new_kwargs = func_call.transform_sources_in_args_kwargs(
        transform_data_source_func=_transform_data_quib,
        transform_parameter_func=_transform_parameter_quib
    )

    return SourceFuncCall.from_(func_call.func, new_args, new_kwargs,
        data_source_locations=func_call.data_source_locations,
        parameter_source_locations=func_call.parameter_source_locations,
        func_definition=func_call.func_definition,
    ), data_sources_to_quibs


def get_func_call_for_translation_without_sources_metadata(func_call: QuibFuncCall):
    """
    Get a source func call along with the newly created data sources to the quibs they represent
    Sources will NOT be with their shape and type- any attempt to access a sources value will raise an exception
    """
    data_sources_to_quibs = {}

    def _transform_data_quib(quib):
        source = NoMetadataSource()
        data_sources_to_quibs[source] = quib
        return source

    def _transform_parameter_quib(quib):
        return Source(quib.get_value_valid_at_path([]))

    new_args, new_kwargs = func_call.transform_sources_in_args_kwargs(
        transform_data_source_func=_transform_data_quib,
        transform_parameter_func=_transform_parameter_quib
    )

    return SourceFuncCall.from_(func_call.func, new_args, new_kwargs,
        data_source_locations=func_call.data_source_locations,
        parameter_source_locations=func_call.parameter_source_locations,
        func_definition=func_call.func_definition,
    ), data_sources_to_quibs
