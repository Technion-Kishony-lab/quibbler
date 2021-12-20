import numpy as np

from pyquibbler import Assignment
from pyquibbler.refactor.inversion.inverter import Inverter
from pyquibbler.refactor.translation.translate import backwards_translate
from pyquibbler.refactor.translation.types import Inversal


class GetItemInverter(Inverter):

    def get_inversals(self):
        sources_to_paths_in_sources = backwards_translate(
            func=self._func_with_args_values.func,
            args=self._func_with_args_values.args_values.args,
            kwargs=self._func_with_args_values.args_values.kwargs,
            path=self._assignment.path,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result)
        )
        assert len(sources_to_paths_in_sources) == 1

        source = list(sources_to_paths_in_sources.keys())[0]
        path_in_source = sources_to_paths_in_sources[source]

        return [
            Inversal(
                assignment=Assignment(
                    path=path_in_source,
                    value=self._assignment.value
                ),
                source=source
            )
        ]
