import functools
from dataclasses import dataclass
from typing import Optional, Union, Any, Dict

from matplotlib.widgets import AxesWidget

from pyquibbler.quib.assignment import Path
from pyquibbler.quib.function_quibs.external_call_failed_exception_handling import \
    external_call_failed_exception_handling
from pyquibbler.refactor.quib.function_runners.function_runner import FunctionRunner
from pyquibbler.quib.utils import QuibRef
from pyquibbler.refactor.graphics.graphics_collection import GraphicsCollection
from pyquibbler.refactor.quib.iterators import recursively_run_func_on_object
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.quib.translation_utils import get_func_with_args_values_for_translation
from pyquibbler.refactor.translation.translate import NoTranslatorsFoundException, backwards_translate
from pyquibbler.refactor.translation.types import Source


@dataclass
class DefaultFunctionRunner(FunctionRunner):

    def _backwards_translate_path(self, valid_path: Path) -> Dict[Quib, Path]:
        # TODO: try without shape/type + args
        func_with_args_values, sources_to_quibs = get_func_with_args_values_for_translation(self.func_with_args_values,
                                                                                            {})

        if not sources_to_quibs:
            return {}

        from pyquibbler.refactor.overriding import CannotFindDefinitionForFunctionException
        try:
            sources_to_paths = backwards_translate(
                func_with_args_values=func_with_args_values,
                path=valid_path,
                shape=self.get_shape(),
                type_=self.get_type()
            )
        except CannotFindDefinitionForFunctionException:
            return {}
        # TODO: make these try excepts singular
        except NoTranslatorsFoundException:
            return {}

        return {
            quib: sources_to_paths.get(source, None)
            for source, quib in sources_to_quibs.items()
        }

    def _replace_sub_argument_with_value(self, quibs_to_paths, inner_arg: Union[Source, Any]):
        """
        Replace an argument, potentially a quib, with it's relevant value, given a map of quibs_to_paths, which
        describes for each quib what path it needs to be valid at
        """
        if isinstance(inner_arg, QuibRef):
            return inner_arg.quib

        if isinstance(inner_arg, Quib):
            if inner_arg in quibs_to_paths:
                path = quibs_to_paths[inner_arg]
            elif self.is_quib_a_data_source(inner_arg):
                # If the quib is a data source, and we didn't see it in the result, we don't need it to be valid at any
                # paths (it did not appear in quibs_to_paths)
                path = None
            else:
                # This is a paramater quib- we always need a parameter quib to be completely valid regardless of where
                # we need ourselves (this quib) to be valid
                path = []

            return inner_arg.get_value_valid_at_path(path)

        return inner_arg

    def _prepare_args_for_call(self, valid_path: Optional[Path]):
        """
        Prepare arguments to call self.func with - replace quibs with values valid at the given path,
        and QuibRefs with quibs.
        """
        quibs_to_paths = {} if valid_path is None else self._backwards_translate_path(valid_path)
        replace_func = functools.partial(self._replace_sub_argument_with_value, quibs_to_paths)
        new_args = [recursively_run_func_on_object(replace_func, arg) for arg in self.args]
        new_kwargs = {key: recursively_run_func_on_object(replace_func, val) for key, val in self.kwargs.items()}
        return new_args, new_kwargs

    def _run_on_path(self, valid_path: Path):

        graphics_collection: GraphicsCollection = self.graphics_collections[()]

        # TODO: quib_guard quib guard

        with graphics_collection.track_and_handle_new_graphics(
                kwargs_specified_in_artists_creation=set(self.kwargs.keys())
        ):
            if self.call_func_with_quibs:
                new_args, new_kwargs = self.args, self.kwargs
            else:
                new_args, new_kwargs = self._prepare_args_for_call(valid_path)

            with external_call_failed_exception_handling():
                res = self.func(*new_args, **new_kwargs)

                # TODO: Move this logic somewhere else
                if len(graphics_collection.widgets) > 0 and isinstance(res, AxesWidget):
                    assert len(graphics_collection.widgets) == 1
                    res = list(graphics_collection.widgets)[0]

                # We don't allow returning quibs as results from functions
                from pyquibbler.quib import Quib
                if isinstance(res, Quib):
                    res = res.get_value()
                ####

                return res
