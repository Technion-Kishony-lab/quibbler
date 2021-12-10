from operator import getitem

import numpy as np
from typing import Set, Any, List, Dict, Callable, Union

from pyquibbler import Assignment
from pyquibbler.path_translators.inversal_types import Source, Inversal
from pyquibbler.path_translators.inverter import Inverter
from pyquibbler.path_translators.utils import call_func_with_values
from pyquibbler.quib import PathComponent
from pyquibbler.quib.assignment.assignment import Path
from pyquibbler.quib.assignment.utils import deep_assign_data_in_path
from pyquibbler.quib.function_quibs.utils import ArgsValues, FuncWithArgsValues, \
    create_empty_array_with_values_at_indices
from pyquibbler.quib.refactor.iterators import recursively_run_func_on_object, SHALLOW_MAX_DEPTH, SHALLOW_MAX_LENGTH
from pyquibbler.quib.refactor.utils import deep_copy_without_quibs_or_graphics
from pyquibbler.utils import convert_args_and_kwargs


class TranspositionalInverter(Inverter):

    SUPPORTING_FUNCS = {np.transpose, np.rot90, np.full, np.concatenate, np.repeat, np.reshape, np.array, getitem}

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

    def _get_data_sources_to_masks(self):
        """
        Get a mapping between quibs and a bool mask representing all the elements that are relevant to them in the
        result
        """
        data_sources_ids_mask = self._get_data_source_ids_mask()
        return {data_source: np.equal(data_sources_ids_mask, id(data_source))
                for data_source in self._get_data_sources()}

    def _convert_data_sources_in_args(self, convert_data_source: Callable):
        """
        Return self.args and self.kwargs with all data source args converted with the given convert_data_source
        callback.
        """
        def _convert_arg(_i, arg):
            def _convert_object(o):
                if isinstance(o, Source):
                    if o in self._get_data_sources():
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
        data_sources_to_masks = self._get_data_sources_to_masks()

        def replace_data_source_with_index_at_dimension(d):
            return np.indices(np.shape(d.value) if isinstance(d, Source) else np.shape(d))[dimension]

        args, kwargs = self._convert_data_sources_in_args(replace_data_source_with_index_at_dimension)
        indices_res = call_func_with_values(self._func_with_args_values.func, args, kwargs)

        return {
            data_source: indices_res[np.logical_and(data_sources_to_masks[data_source], relevant_indices_mask)]
            for data_source in self._get_data_sources()
        }

    def _get_data_sources_to_indices_in_quibs(self) -> Dict[Source, np.ndarray]:
        """
        Get a mapping of quibs to the quib's indices that were referenced in `self._indices` (ie after inversion of the
        indices relevant to the particular quib)
        """
        relevant_indices_mask = create_empty_array_with_values_at_indices(
            indices=self._working_component,
            shape=np.shape(self._previous_result),
            value=True,
            empty_value=False
        )
        data_sources = self._get_data_sources()
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

    def _get_data_sources_to_inverted_paths(self) -> Dict[Source, Path]:
        data_sources_to_indices = self._get_data_sources_to_indices_in_quibs()
        return {
            data_source: [PathComponent(component=data_sources_to_indices[data_source], indexed_cls=np.ndarray)]
            if data_sources_to_indices[data_source] is not None else []
            for data_source in data_sources_to_indices
        }

    def _get_result_with_assignment_set(self):
        new_result = deep_copy_without_quibs_or_graphics(self._previous_result)
        return deep_assign_data_in_path(new_result, self._assignment.path, self._assignment.value)

    def _get_relevant_result_values(self) -> Dict[Source, np.ndarray]:
        """
        Get a mapping of quibs to values that were both referenced in `self._indices` and came from the
        corresponding quib
        """
        result_bool_mask = create_empty_array_with_values_at_indices(np.shape(self._previous_result),
                                                                     indices=self._working_component,
                                                                     value=True,
                                                                     empty_value=False)
        representative_result_value = self._get_result_with_assignment_set()
        sources_to_masks = self._get_data_sources_to_masks()

        return {
            data_source: representative_result_value[np.logical_and(sources_to_masks[data_source], result_bool_mask)]
            for data_source in self._get_data_sources()
        }

    @property
    def _working_component(self):
        return self._assignment.path[0].component if len(self._assignment.path) > 0 else True

    def get_inversals(self):
        sources_to_values = self._get_relevant_result_values()
        sources_to_paths = self._get_data_sources_to_inverted_paths()
        return [
            Inversal(
                source=data_source,
                assignment=Assignment(
                    path=path,
                    value=sources_to_values[data_source]
                )
            )
            for data_source, path in sources_to_paths.items()
            if data_source in sources_to_values
        ]
