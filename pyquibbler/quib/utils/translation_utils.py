from __future__ import annotations
from typing import TYPE_CHECKING

from pyquibbler.translation.types import Source
from pyquibbler.translation.source_func_call import SourceFuncCall


if TYPE_CHECKING:
    from pyquibbler.quib.func_calling import QuibFuncCall


def get_func_call_for_translation(func_call: QuibFuncCall):
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

    return SourceFuncCall.from_(
        data_source_locations=func_call.data_source_locations,
        parameter_source_locations=func_call.parameter_source_locations,
        func=func_call.func,
        func_args=new_args,
        func_kwargs=new_kwargs,
        include_defaults=True
    ), data_sources_to_quibs
