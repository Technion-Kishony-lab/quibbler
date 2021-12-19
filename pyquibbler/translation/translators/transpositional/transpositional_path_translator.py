from abc import abstractmethod
from functools import lru_cache
from operator import getitem

import numpy as np
from typing import Dict, Callable, Any, List, Set

from pyquibbler.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.translation.forwards_path_translator import ForwardsPathTranslator
from pyquibbler.translation.translators.transpositional.utils import get_data_source_ids_mask
from pyquibbler.translation.types import Source
from pyquibbler.translation.utils import call_func_with_values
from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment import Path
from pyquibbler.quib.assignment.assignment import working_component
from pyquibbler.quib.function_quibs.utils import create_empty_array_with_values_at_indices
from pyquibbler.quib.refactor.iterators import recursively_run_func_on_object, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH
from pyquibbler.utils import convert_args_and_kwargs


class BackwardsTranspositionalTranslator(BackwardsPathTranslator):

    def _get_data_source_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """

        def replace_source_with_id(obj):
            if isinstance(obj, Source):
                return np.full(np.shape(obj.value), id(obj))
            return obj

        args, kwargs = self._convert_data_sources_in_args(replace_source_with_id)
        return call_func_with_values(self.func, args, kwargs)

    def get_data_sources_to_masks_in_result(self) -> Dict[Source, Any]:
        """
        Get a mapping between quibs and a bool mask representing all the elements that are relevant to them in the
        result
        """
        data_sources_ids_mask = self._get_data_source_ids_mask()
        return {data_source: np.equal(data_sources_ids_mask, id(data_source))
                for data_source in self.get_data_sources()}

    def _convert_data_sources_in_args(self, convert_data_source: Callable):
        """
        Return self.args and self.kwargs with all data source args converted with the given convert_data_source
        callback.
        """
        def _convert_arg(_i, arg):
            def _convert_object(o):
                if isinstance(o, Source):
                    if o in self.get_data_sources():
                        return convert_data_source(o)
                    return o.value
                return o

            return recursively_run_func_on_object(func=_convert_object,
                                                  obj=arg,
                                                  max_depth=SHALLOW_MAX_DEPTH,
                                                  max_length=SHALLOW_MAX_LENGTH)

        return convert_args_and_kwargs(_convert_arg,
                                       self.args_values.args,
                                       self.args_values.kwargs)

    def _get_data_sources_to_indices_at_dimension(self, dimension: int, relevant_indices_mask) -> Dict[Source, np.ndarray]:
        """
        Get a mapping of quibs to their referenced indices at a *specific dimension*
        """
        data_sources_to_masks = self.get_data_sources_to_masks_in_result()

        def replace_data_source_with_index_at_dimension(d):
            return np.indices(np.shape(d.value) if isinstance(d, Source) else np.shape(d))[dimension]

        args, kwargs = self._convert_data_sources_in_args(replace_data_source_with_index_at_dimension)
        indices_res = call_func_with_values(self._func_with_args_values.func, args, kwargs)

        return {
            data_source: indices_res[np.logical_and(data_sources_to_masks[data_source], relevant_indices_mask)]
            for data_source in self.get_data_sources()
        }

    def _get_data_sources_to_indices_in_data_sources(self) -> Dict[Source, np.ndarray]:
        """
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after inversion of the
        indices relevant to the particular quib)
        """
        relevant_indices_mask = create_empty_array_with_values_at_indices(
            indices=self._working_component,
            shape=self._shape,
            value=True,
            empty_value=False
        )
        data_sources = self.get_data_sources()
        max_shape_length = max([np.ndim(data_source_argument.value)
                                for data_source_argument in data_sources]) if len(data_sources) > 0 else 0

        # Default is to set all - if we have a shape we'll change this TODO: does this make sense??
        data_sources_to_indices = {
            data_source: None for data_source in data_sources
        }
        for i in range(max_shape_length):
            data_sources_to_indices_at_dimension = self._get_data_sources_to_indices_at_dimension(i,
                                                                                                  relevant_indices_mask)

            for data_source, index in data_sources_to_indices_at_dimension.items():
                if data_sources_to_indices[data_source] is None:
                    data_sources_to_indices[data_source] = tuple()
                data_sources_to_indices[data_source] = (*data_sources_to_indices[data_source], index)

        return {
            data_source: indices
            for data_source, indices in data_sources_to_indices.items()
            if indices is None or all(
                len(dim) > 0
                for dim in indices
            )
        }

    def translate_in_order(self) -> Dict[Source, Path]:
        data_sources_to_indices = self._get_data_sources_to_indices_in_data_sources()
        return {
            data_source: [PathComponent(component=data_sources_to_indices[data_source], indexed_cls=np.ndarray)]
            if data_sources_to_indices[data_source] is not None else []
            for data_source in data_sources_to_indices
        }


class ForwardsTranspositionalTranslator(ForwardsPathTranslator):

    @lru_cache()
    def _get_source_ids_mask(self):
        return get_data_source_ids_mask(self._func_with_args_values, {
            source: working_component(path)
            for source, path in self._sources_to_paths.items()
        })

    def _translate_forwards_source_with_path(self, source: Source, path: Path) -> Path:
        """
        There are two things we can potentially do:
        1. Translate the invalidation path given the current function quib (eg if this function quib is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        3. Pass on the current path to all our children
        """
        if len(path) > 0 and path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return path

        return [PathComponent(component=np.equal(self._get_source_ids_mask(), id(source)),
                              indexed_cls=np.ndarray), *path[1:]]

    def translate(self) -> Dict[Source, List[Path]]:
        return {
            source: [self._translate_forwards_source_with_path(source, path)]
            for source, path in self._sources_to_paths.items()
        }
