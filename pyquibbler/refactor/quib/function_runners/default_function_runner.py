from dataclasses import dataclass
from typing import Dict

from pyquibbler.refactor.path.path_component import Path
from pyquibbler.refactor.quib.function_runners.function_runner import FunctionRunner
from pyquibbler.refactor.graphics.graphics_collection import GraphicsCollection
from pyquibbler.refactor.quib.quib import Quib
from pyquibbler.refactor.quib.translation_utils import get_func_call_for_translation
from pyquibbler.refactor.quib.func_call_utils import get_func_call_with_quibs_valid_at_paths, get_data_source_quibs
from pyquibbler.refactor.translation.translate import NoTranslatorsFoundException, backwards_translate


@dataclass
class DefaultFunctionRunner(FunctionRunner):

    def _backwards_translate_path(self, valid_path: Path) -> Dict[Quib, Path]:
        if not get_data_source_quibs(self.func_call):
            return {}

        # TODO: try without shape/type + args
        func_call, sources_to_quibs = get_func_call_for_translation(self.func_call,  {})

        try:
            sources_to_paths = backwards_translate(
                func_call=func_call,
                path=valid_path,
                shape=self.get_shape(),
                type_=self.get_type(),
                **self.get_result_metadata()
            )
        except NoTranslatorsFoundException:
            return {}

        return {
            quib: sources_to_paths.get(source, None)
            for source, quib in sources_to_quibs.items()
        }

    def _run_on_path(self, valid_path: Path):
        graphics_collection: GraphicsCollection = self.graphics_collections[()]

        if self.call_func_with_quibs:
            ready_to_run_func_call = self.func_call
        else:
            quibs_to_paths = {} if valid_path is None else self._backwards_translate_path(valid_path)
            ready_to_run_func_call = get_func_call_with_quibs_valid_at_paths(self.func_call, quibs_to_paths)

        return self._run_single_call(
            func=ready_to_run_func_call.func,
            args=ready_to_run_func_call.args,
            kwargs=ready_to_run_func_call.kwargs,
            graphics_collection=graphics_collection,
            quibs_to_guard=set()
        )
