from typing import Dict

from pyquibbler.utilities.iterators import iter_objects_of_type_in_object_recursively
from pyquibbler.path import Path, Paths, split_path_at_end_of_object

from ..base_translators import BackwardsTranslationRunCondition, BackwardsPathTranslator, ForwardsPathTranslator
from ..types import Source


class Obj2QuibBackwardsPathTranslator(BackwardsPathTranslator):

    RUN_CONDITIONS = [BackwardsTranslationRunCondition.NO_SHAPE_AND_TYPE]

    def _backwards_translate(self) -> Dict[Source, Path]:
        path_within_object, remaining_path, obj = split_path_at_end_of_object(self._func_call.args[0], self._path)

        if isinstance(obj, Source):
            return {obj: remaining_path}

        sources_within_the_referenced_path = iter_objects_of_type_in_object_recursively(Source, obj)
        return {source: [] for source in sources_within_the_referenced_path}


class Obj2QuibForwardsPathTranslator(ForwardsPathTranslator):

    def _forward_translate(self) -> Paths:
        return [self._source_location.path + self._path]
