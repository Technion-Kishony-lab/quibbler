from typing import Dict

from pyquibbler.quib.assignment import Path
from pyquibbler.refactor.func_call import FuncCall
from pyquibbler.refactor.iterators import iter_objects_of_type_in_object_shallowly
from pyquibbler.refactor.quib.iterators import recursively_run_func_on_object, SHALLOW_MAX_DEPTH
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.translation.types import Source
from pyquibbler.utils import convert_args_and_kwargs


def get_data_source_quibs(func_with_args_values: FuncCall):
    return set(iter_objects_of_type_in_object_shallowly(Quib,  func_with_args_values.get_data_source_arguments()))


def get_func_with_args_values_for_translation(func_with_args_values, data_source_quibs_to_paths: Dict[Quib, Path]):
    data_source_quibs = get_data_source_quibs(func_with_args_values)
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
                                           func_with_args_values.args,
                                           func_with_args_values.kwargs)
    return FuncCall.from_function_call(
        func=func_with_args_values.func,
        args=args,
        kwargs=kwargs,
        include_defaults=False
    ), data_sources_to_quibs