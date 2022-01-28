import numpy as np

from pyquibbler.path.data_accessing import deep_get
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.assignment import Assignment
from pyquibbler.translation.translators import BackwardsTranspositionalTranslator, ForwardsTranspositionalTranslator
from pyquibbler.translation.types import Inversal
from pyquibbler.path.path_component import PathComponent
from pyquibbler.path.utils import working_component
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices


class TranspositionalInverter(Inverter):

    def _create_inversals_from_paths(self, sources_to_paths_in_sources, sources_to_single_paths_in_result):
        representative_result_value = self._get_result_with_assignment_set()

        inversals = []
        for data_source, path in sources_to_paths_in_sources.items():
            if data_source in sources_to_single_paths_in_result:
                path_in_result = sources_to_single_paths_in_result[data_source]
                assignment_value = deep_get(representative_result_value, path_in_result)

                # The forwards translation of TranspositionalTranslator
                # does not promise to get a correct shape given the path it translates-
                # for example, given
                # `np.transpose(a), path=[PathComponent(np.ndarray, component=0)]`
                # with `a` as the forward translated ndarray source, it could translate this to
                # np.array([True, False, False, ...]) (of course matching shape of result)
                # Even though this now means that the result of `deep_get` will be a 1d array.
                # We check if we want to load this as a single object if the assignment_value is an ndarray, and the
                # path in the source referenced a single value
                load_as_single = isinstance(assignment_value, np.ndarray) and not isinstance(
                    deep_get(data_source.value, path), np.ndarray
                )
                if load_as_single:
                    flattened = np.array(assignment_value.flat)
                    assert len(flattened) == 1
                    assignment_value = assignment_value.flat[0]

                inversals.append(Inversal(
                    source=data_source,
                    assignment=Assignment(
                        path=path,
                        value=assignment_value
                    )
                ))
        return inversals

    def get_inversals(self):
        from pyquibbler.utilities.numpy_original_functions import np_logical_and

        sources_to_paths_in_sources = BackwardsTranspositionalTranslator(
            func_call=self._func_call,
            path=self._assignment.path,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result)
        ).translate()
        sources_to_paths_in_result = ForwardsTranspositionalTranslator(
            func_call=self._func_call,
            sources_to_paths=sources_to_paths_in_sources,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result),
            should_forward_empty_paths_to_empty_paths=False
        ).translate()
        assert all(len(paths) == 1 for paths in sources_to_paths_in_result.values())

        boolean_mask = create_bool_mask_with_true_at_indices(np.shape(self._previous_result),
                                                             working_component(self._assignment.path))

        sources_to_single_paths_in_result = {}
        for source, paths in sources_to_paths_in_result.items():
            path = paths[0]
            if len(path) > 0 and path[0].indexed_cls == np.ndarray:
                path[0] = PathComponent(
                    indexed_cls=np.ndarray,
                    component=np_logical_and(working_component(path), boolean_mask)
                )
            elif len(path) == 0:
                path.insert(0, PathComponent(
                    indexed_cls=np.ndarray,
                    component=boolean_mask
                ))
            sources_to_single_paths_in_result[source] = path

        return self._create_inversals_from_paths(sources_to_paths_in_sources, sources_to_single_paths_in_result)
