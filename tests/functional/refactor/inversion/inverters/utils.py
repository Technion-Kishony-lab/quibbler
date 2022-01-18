from typing import Callable, Any, Tuple, Mapping

from pyquibbler import Assignment
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.inversion.invert import invert
from pyquibbler.path.data_accessing import deep_assign_data_in_path
from pyquibbler.quib.factory import get_original_func
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.utils import call_func_with_sources_values
from pyquibbler.path import PathComponent


def inverse(func: Callable, indices: Any, value: Any, args: Tuple[Any, ...] = None, kwargs: Mapping[str, Any] = None,
            empty_path: bool = False):
    func = get_original_func(func)
    if indices is not None and empty_path is True:
        raise Exception("The indices cannot be set if empty path is True")

    args = args or tuple()
    kwargs = kwargs or {}
    previous_value = call_func_with_sources_values(func, args, kwargs)
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