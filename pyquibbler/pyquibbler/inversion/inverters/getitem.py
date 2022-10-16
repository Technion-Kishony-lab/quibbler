import numpy as np

from pyquibbler.assignment.assignment import create_assignment_from_nominal_down_up_values
from pyquibbler.path_translation.base_translators import BackwardsTranslationRunCondition
from pyquibbler.path_translation.translate import backwards_translate
from pyquibbler.path_translation.types import Inversal

from ..inverter import Inverter


class GetItemInverter(Inverter):

    def get_inversals(self):
        sources_to_paths_in_sources = backwards_translate(
            run_condition=BackwardsTranslationRunCondition.WITH_SHAPE_AND_TYPE,
            func_call=self._func_call,
            path=self._assignment.path,
            shape=np.shape(self._previous_result),
            type_=type(self._previous_result)
        )
        if len(sources_to_paths_in_sources) != 1:
            self._raise_run_failed_exception()

        source = list(sources_to_paths_in_sources.keys())[0]
        path_in_source = sources_to_paths_in_sources[source]
        nominal_down_up_values = self._get_assignment_nominal_down_up_values()
        new_assignment = create_assignment_from_nominal_down_up_values(nominal_down_up_values=nominal_down_up_values,
                                                                       path=path_in_source)
        return [Inversal(source=source, assignment=new_assignment)]
