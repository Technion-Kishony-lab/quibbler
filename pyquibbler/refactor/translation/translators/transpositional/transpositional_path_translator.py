import functools
from functools import lru_cache

import numpy as np
from typing import Dict, Callable, Any, List

from pyquibbler.refactor.translation.backwards_path_translator import BackwardsPathTranslator
from pyquibbler.refactor.translation.numpy_forwards_path_translator import NumpyForwardsPathTranslator
from pyquibbler.refactor.translation.numpy_translator import NumpyBackwardsPathTranslator
from pyquibbler.refactor.translation.translators.transpositional.utils import get_data_source_ids_mask
from pyquibbler.refactor.translation.types import Source
from pyquibbler.refactor.translation.utils import call_func_with_sources_values
from pyquibbler.refactor.path.path_component import Path, PathComponent
from pyquibbler.refactor.path.utils import working_component
from pyquibbler.refactor.utilities.general_utils import create_empty_array_with_values_at_indices
from pyquibbler.refactor.utilities.iterators import recursively_run_func_on_object, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH
from pyquibbler.utils import convert_args_and_kwargs


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_data_source_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each quib's ids instead of it's values
        """

        def replace_source_with_id(obj):
            if isinstance(obj, Source):
                return np.full(np.shape(obj.value), id(obj))
            return obj

        args, kwargs = self._convert_data_sources_in_args(replace_source_with_id)
        return call_func_with_sources_values(self.func, args, kwargs)

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
        indices_res = call_func_with_sources_values(self._func_call.func, args, kwargs)

        return {
            data_source: indices_res[np.logical_and(data_sources_to_masks[data_source], relevant_indices_mask)]
            for data_source in self.get_data_sources()
        }

    @functools.lru_cache()
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

    @property
    def _working_component(self):
        # TODO: this is a bug in the previous version as well: Is this the solution we want?
        # This bug is when a string is our first arg - for example, if we have a field array.
        # What if we have indices right after field?
        component = super(BackwardsTranspositionalTranslator, self)._working_component
        if isinstance(component, str):
            return True
        return component

    def _get_path_in_source(self, source: Source, path_in_result: Path):
        # This is cached, will only run once
        data_sources_to_indices = self._get_data_sources_to_indices_in_data_sources()

        if source not in data_sources_to_indices:
            return None

        if data_sources_to_indices[source] is None:
            # TODO: Is this really what we want?
            return []

        return [PathComponent(component=data_sources_to_indices[source], indexed_cls=np.ndarray)]


class ForwardsTranspositionalTranslator(NumpyForwardsPathTranslator):

    @lru_cache()
    def _get_source_ids_mask(self):
        return get_data_source_ids_mask(self._func_call, {
            source: working_component(path)
            for source, path in self._sources_to_paths.items()
        })

    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        return np.equal(self._get_source_ids_mask(), id(source))

    def _forward_translate_source(self, source: Source, path: Path) -> List[Path]:
        """
        There are two things we can potentially do:
        1. Translate the invalidation path given the current function quib (eg if this function quib is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        2. Pass on the current path to all our children
        """
        if len(path) > 0 and path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return [path]

        return super(ForwardsTranspositionalTranslator, self)._forward_translate_source(source, path)

