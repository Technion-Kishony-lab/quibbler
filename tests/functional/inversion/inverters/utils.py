from typing import Callable, Any, Tuple, Mapping

from pyquibbler import Assignment
from pyquibbler.inversion.invert import invert
from pyquibbler.path.data_accessing import deep_set
from pyquibbler.utilities.get_original_func import get_original_func
from pyquibbler.path_translation.source_func_call import SourceFuncCall
from pyquibbler.path import PathComponent


def inverse(func: Callable, indices: Any, value: Any, args: Tuple[Any, ...] = None, kwargs: Mapping[str, Any] = None,
            empty_path: bool = False, assignment: Assignment = None):
    func = get_original_func(func)
    if indices is not None and empty_path is True:
        raise Exception("The indices cannot be set if empty path is True")

    args = args or tuple()
    kwargs = kwargs or {}
    previous_value = SourceFuncCall.from_(func, args, kwargs).run()
    assignment = assignment or Assignment(path=[PathComponent(indices)] if not empty_path else [], value=value)
    inversals = invert(
        func_call=SourceFuncCall.from_(func, args, kwargs),
        previous_result=previous_value,
        assignment=assignment
    )

    return ({
                inversal.source: deep_set(inversal.source.value, inversal.assignment.path, inversal.assignment.value)
                for inversal in inversals
            },
            inversals)

