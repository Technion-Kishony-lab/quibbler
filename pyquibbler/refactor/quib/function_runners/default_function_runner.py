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
from pyquibbler.refactor.quib.translation_utils import get_func_call_for_translation
from pyquibbler.refactor.quib.func_call_utils import is_quib_a_data_source, get_func_call_with_quibs_valid_at_paths
from pyquibbler.refactor.translation.translate import NoTranslatorsFoundException, backwards_translate
from pyquibbler.refactor.translation.types import Source


@dataclass
class DefaultFunctionRunner(FunctionRunner):

    def _backwards_translate_path(self, valid_path: Path) -> Dict[Quib, Path]:
        # TODO: try without shape/type + args
        func_call, sources_to_quibs = get_func_call_for_translation(self.func_call,
                                                                                            {})

        if not sources_to_quibs:
            return {}

        from pyquibbler.refactor.overriding import CannotFindDefinitionForFunctionException
        try:
            sources_to_paths = backwards_translate(
                func_call=func_call,
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

    def _run_on_path(self, valid_path: Path):

        graphics_collection: GraphicsCollection = self.graphics_collections[()]

        # TODO: quib_guard quib guard

        with graphics_collection.track_and_handle_new_graphics(
                kwargs_specified_in_artists_creation=set(self.kwargs.keys())
        ):
            if self.call_func_with_quibs:
                ready_to_run_func_call = self.func_call
            else:
                quibs_to_paths = {} if valid_path is None else self._backwards_translate_path(valid_path)
                ready_to_run_func_call = get_func_call_with_quibs_valid_at_paths(self.func_call, quibs_to_paths)

            with external_call_failed_exception_handling():
                res = self.func(*ready_to_run_func_call.args, **ready_to_run_func_call.kwargs)

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
