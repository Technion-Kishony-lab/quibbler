from __future__ import annotations

from .types import Source, NoMetadataSource
from .source_func_call import SourceFuncCall

from typing import TYPE_CHECKING, Optional, Tuple, Dict

if TYPE_CHECKING:
    from pyquibbler.quib.func_calling import QuibFuncCall
    from pyquibbler.quib.quib import Quib


def get_func_call_for_translation(func_call: QuibFuncCall, with_meta_data: Optional[bool] = None
                                  ) -> Tuple[SourceFuncCall, Dict[Source, Quib]]:
    """
    Get a source func call along with the newly created data sources to the quibs they represent

    with_meta_data = True:
        All data sources will be in correct shape and type

    with_meta_data = False:
        All data sources will be NoMetadataSource

    with_meta_data = None:
        Use Source if metadata is available, otherwise use NoMetadataSource


    """
    data_sources_to_quibs = {}

    def _transform_data_quib(quib: Quib):
        if with_meta_data is True \
                or with_meta_data is None and quib.handler.quib_function_call.result_shape is not None:
            source = Source(quib.get_value_valid_at_path(None))
        else:
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
