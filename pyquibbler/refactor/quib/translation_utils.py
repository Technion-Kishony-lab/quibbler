from typing import Dict

from pyquibbler.quib.assignment import Path
from pyquibbler.refactor.func_call import FuncCall
from pyquibbler.refactor.quib.func_call_utils import get_data_source_quibs
from pyquibbler.refactor.quib.iterators import recursively_run_func_on_object, SHALLOW_MAX_DEPTH
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.translation.types import Source
from pyquibbler.utils import convert_args_and_kwargs


def get_func_call_for_translation(func_call: FuncCall, data_source_quibs_to_paths: Dict[Quib, Path]):
    data_source_quibs = get_data_source_quibs(func_call)
    data_sources_to_quibs = {}

    def _replace_quib_with_source(_, arg):
        def _replace(q):
            if isinstance(q, Quib):
                if q in data_source_quibs:
                    source = Source(q.get_value_valid_at_path(data_source_quibs_to_paths.get(q)))
                    data_sources_to_quibs[source] = q
                else:
                    source = Source(q.get_value_valid_at_path([]))
                return source
            return q

        return recursively_run_func_on_object(_replace, arg, max_depth=SHALLOW_MAX_DEPTH)

    args, kwargs = convert_args_and_kwargs(_replace_quib_with_source,
                                           func_call.args,
                                           func_call.kwargs)
    return FuncCall.from_function_call(
        func=func_call.func,
        args=args,
        kwargs=kwargs,
        include_defaults=False
    ), data_sources_to_quibs
