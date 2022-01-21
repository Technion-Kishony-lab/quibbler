import numpy as np

from pyquibbler.path.data_accessing import deep_get
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.assignment import Assignment
from pyquibbler.translation.types import Inversal
from pyquibbler.path.path_component import PathComponent
from pyquibbler.path.utils import working_component
from pyquibbler.utilities.general_utils import create_bool_mask_with_true_at_indices
from pyquibbler.translation.translate import backwards_translate, forwards_translate


class TranspositionalInverter(Inverter):

    def get_inversals(self):
        sources_to_paths_in_sources = backwards_translate(
            func_call=self._func_call,
            path=self._assignment.path,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result)
        )
        sources_to_paths_in_result = forwards_translate(
            func_call=self._func_call,
            sources_to_paths=sources_to_paths_in_sources,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result)
        )

        boolean_mask = create_bool_mask_with_true_at_indices(np.shape(self._previous_result), working_component(self._assignment.path))
        assert all(len(paths) == 1 for paths in sources_to_paths_in_result.values())

        sources_to_paths_in_result = {
            source: [PathComponent(component=np.logical_and(working_component(paths[0]), boolean_mask),
                                   indexed_cls=np.ndarray), *paths[0][1:]]
            for source, paths in sources_to_paths_in_result.items()
        }

        representative_result_value = self._get_result_with_assignment_set()

        return [
            Inversal(
                source=data_source,
                assignment=Assignment(
                    path=path,
                    # we asserted above there is only one path per forwards translation
                    value=deep_get(representative_result_value, sources_to_paths_in_result[data_source])
                )
            )
            for data_source, path in sources_to_paths_in_sources.items()
            if data_source in sources_to_paths_in_result
        ]
