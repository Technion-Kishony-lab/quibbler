import functools

import numpy as np
from typing import Dict, Any

from pyquibbler.function_definitions import SourceLocation
from pyquibbler.translation.numpy_translator import NumpyForwardsPathTranslator
from pyquibbler.translation.numpy_translator import NumpyBackwardsPathTranslator
from pyquibbler.translation.source_func_call import SourceFuncCall
from pyquibbler.translation.translators.transpositional.utils import get_data_source_ids_mask
from pyquibbler.translation.types import Source
from pyquibbler.path.path_component import Path, Paths, PathComponent
from pyquibbler.path.utils import working_component_of_type
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices
from pyquibbler.utils import get_original_func


class BackwardsTranspositionalTranslator(NumpyBackwardsPathTranslator):

    def _get_shape_to_fill_for_data_source_in_location(self, location: SourceLocation):
        """
        Return the shape that needs to be filled for a given data source. One might think this is simply the shape of
        the data source (whether it be minor or major),
        but in situations in which a minor data source is not part of the shape (or only part of it
        is a part of the shape) of the major data source (for example, `a` in `a = [1, 2],
         b = np.array([1, 2, a])`), we want to return only the part of the shape that is relevant to the major data
         source
        """
        # TODO: Functions should allow specifying "major" data sources at a full path instead of just at argument level
        # Because of situations like concat, in which the "major" data source is one level in (within a tuple of the
        # first arg)
        if self._func_call.func == get_original_func(np.concatenate):
            major_data_source_location = type(location)(argument=location.argument, path=[location.path[0]])
        else:
            major_data_source_location = type(location)(argument=location.argument, path=[])

        major_data_source = major_data_source_location.find_in_args_kwargs(self._func_call.args, self._func_call.kwargs)

        # A source cannot be within a source- if the major data argument is already a source, just return it's shape
        if isinstance(major_data_source, Source):
            return np.shape(major_data_source.value)

        major_data_source = np.array(major_data_source)
        minor_source = location.find_in_args_kwargs(self._func_call.args, self._func_call.kwargs)
        return np.shape(minor_source.value)[:major_data_source.ndim - len(location.path)]

    def _get_data_source_ids_mask(self) -> np.ndarray:
        """
        Runs the function with each source's ids instead of it's values
        """
        args = self._func_call.args
        kwargs = self._func_call.kwargs
        for location in self._func_call.data_source_locations:
            shape = self._get_shape_to_fill_for_data_source_in_location(location)
            source = location.find_in_args_kwargs(args, kwargs)
            args, kwargs = location.set_in_args_kwargs(args, kwargs, np.full(shape, id(source)))
        return SourceFuncCall.from_(self._func_call.func, args, kwargs,
                                    data_source_locations=[],
                                    parameter_source_locations=self._func_call.parameter_source_locations,
                                    func_definition=self._func_call.func_definition).run()

    def get_data_sources_to_masks_in_result(self) -> Dict[Source, Any]:
        """
        Get a mapping between sources and a bool mask representing all the elements that are relevant to them in the
        result
        """
        data_sources_ids_mask = self._get_data_source_ids_mask()
        return {data_source: np.equal(data_sources_ids_mask, id(data_source))
                for data_source in self._func_call.get_data_sources()}

    def _get_data_sources_to_indices_at_dimension(self, dimension: int,
                                                  relevant_indices_mask) -> Dict[Source, np.ndarray]:
        """
        Get a mapping of sources to their referenced indices at a *specific dimension*
        """
        data_sources_to_masks = self.get_data_sources_to_masks_in_result()

        args = self._func_call.args
        kwargs = self._func_call.kwargs
        for location in self._func_call.data_source_locations:
            shape = self._get_shape_to_fill_for_data_source_in_location(location)
            arr = np.indices(shape)[dimension]
            args, kwargs = location.set_in_args_kwargs(args, kwargs, arr)

        indices_res = SourceFuncCall.from_(self._func_call.func, args, kwargs,
                                           data_source_locations=[],
                                           parameter_source_locations=self._func_call.parameter_source_locations,
                                           func_definition=self._func_call.func_definition).run()

        return {
            data_source: indices_res[np.logical_and(data_sources_to_masks[data_source], relevant_indices_mask)]
            for data_source in self._func_call.get_data_sources()
        }

    def _get_data_sources_to_paths_in_data_sources(self) -> Dict[Source, np.ndarray]:
        """
        Get a mapping of sources to the source's indices that were referenced in `self._indices`
         (ie after inversion of the indices relevant to the particular source)
        """
        relevant_indices_mask = create_bool_mask_with_true_at_indices(self._shape, self._working_component)
        data_sources = self._func_call.get_data_sources()

        max_shape_length = 0
        for location in self._func_call.data_source_locations:
            shape = self._get_shape_to_fill_for_data_source_in_location(location)
            max_shape_length = max([max_shape_length, len(shape)])

        data_sources_to_masks = self.get_data_sources_to_masks_in_result()

        # Default is to set all for any source that appears in result - if we have a shape we'll change this to be
        # specific per dimension
        data_sources_in_result = {data_source for data_source in data_sources
                                  if np.any(np.logical_and(data_sources_to_masks[data_source], relevant_indices_mask))}
        data_sources_to_indices = {}

        for i in range(max_shape_length):
            data_sources_to_indices_at_dimension = self._get_data_sources_to_indices_at_dimension(i,
                                                                                                  relevant_indices_mask)

            for data_source, indices in data_sources_to_indices_at_dimension.items():
                current_indices = data_sources_to_indices.get(data_source, tuple())
                data_sources_to_indices[data_source] = (*current_indices, indices)

        return {
            data_source:
                [PathComponent(indexed_cls=np.ndarray, component=data_sources_to_indices[data_source])]
                if data_source in data_sources_to_indices else
                []
            for data_source in data_sources_in_result
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

    def _get_path_in_source(self, source: Source):
        # This is cached, will only run once
        data_sources_to_paths = self._get_data_sources_to_paths_in_data_sources()

        if source not in data_sources_to_paths:
            return None

        return data_sources_to_paths[source]


class ForwardsTranspositionalTranslator(NumpyForwardsPathTranslator):

    def _get_source_ids_mask(self):
        return get_data_source_ids_mask(self._func_call, {
            source: working_component_of_type(path, (list, np.ndarray), True)
            for source, path in self._sources_to_paths.items()
        })

    def _forward_translate_indices_to_bool_mask(self, source: Source, indices: Any):
        return np.equal(self._get_source_ids_mask(), id(source))

    def _forward_translate_source(self, source: Source, path: Path) -> Paths:
        """
        There are two things we can potentially do:
        1. Translate the invalidation path given the current function source (eg if this function source is rotate,
        take the invalidated indices, rotate them and invalidate children with the resulting indices)
        2. Pass on the current path to all our children
        """
        if len(path) > 0 and path[0].references_field_in_field_array():
            # The path at the first component references a field, and therefore we cannot translate it given a
            # normal transpositional function (neither does it make any difference, as transpositional functions
            # don't change fields)
            return [path]

        return super(ForwardsTranspositionalTranslator, self)._forward_translate_source(source, path)
