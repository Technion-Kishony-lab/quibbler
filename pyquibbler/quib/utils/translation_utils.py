from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.utilities.iterators import SHALLOW_MAX_DEPTH, recursively_run_func_on_object
from pyquibbler.function_definitions.func_call import FuncCall
from pyquibbler.quib.utils.func_call_utils import get_data_source_quibs
from pyquibbler.quib.quib import Quib
from pyquibbler.translation.types import Source
from pyquibbler.utils import convert_args_and_kwargs


def get_func_call_for_translation(func_call: FuncCall):
    data_source_quibs = get_data_source_quibs(func_call)
    data_sources_to_quibs = {}

    def _replace_quib_with_source(_, arg):
        def _replace(q):
            if isinstance(q, Quib):
                if q in data_source_quibs:
                    source = Source(q.get_value_valid_at_path(None))
                    data_sources_to_quibs[source] = q
                else:
                    source = Source(q.get_value_valid_at_path([]))
                return source
            return q

        return recursively_run_func_on_object(_replace, arg, max_depth=SHALLOW_MAX_DEPTH)

    args, kwargs = convert_args_and_kwargs(_replace_quib_with_source,
                                           func_call.args,
                                           func_call.kwargs)
    return SourceFuncCall.from_(
        func=func_call.func,
        func_args=args,
        func_kwargs=kwargs,
        include_defaults=True
    ), data_sources_to_quibs
