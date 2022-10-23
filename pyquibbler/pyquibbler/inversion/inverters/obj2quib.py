from typing import List

from pyquibbler.assignment.assignment import create_assignment_from_nominal_down_up_values
from pyquibbler.path import split_path_at_end_of_object, deep_get
from pyquibbler.path_translation.types import Inversal, Source
from pyquibbler.utilities.iterators import get_paths_for_objects_of_type

from ..inverter import Inverter


class Obj2QuibInverter(Inverter):
    """
    Invert assignment to obj2quib.
    """
    def get_inversals(self) -> List[Inversal]:
        assignment_path = self._assignment.path
        path_within_object, remaining_path, obj = split_path_at_end_of_object(self._func_call.args[0],
                                                                              path=assignment_path)

        if isinstance(obj, Source):
            # the assignment refers to, or within, a source
            new_assignment = create_assignment_from_nominal_down_up_values(
                nominal_down_up_values=self._get_assignment_nominal_down_up_values(),
                path=remaining_path)
            return [Inversal(assignment=new_assignment, source=obj)]

        # the assignment refers to a non-source object. all sources within this object are assigned full value
        # based on this path within the object, referring to the result with assignment.
        result_nominal_down_up = self._get_result_with_assignment_nominal_down_up()
        paths_to_sources_within_assignment_path = get_paths_for_objects_of_type(obj, Source)
        inversals = []
        for path_to_source_within_assignment_path in paths_to_sources_within_assignment_path:
            source = deep_get(obj, path_to_source_within_assignment_path)
            path_in_result = assignment_path + path_to_source_within_assignment_path
            value_nominal_down_up = [deep_get(result, path_in_result)
                                     for result in result_nominal_down_up]
            new_assignment = create_assignment_from_nominal_down_up_values(
                nominal_down_up_values=value_nominal_down_up,
                path=[])
            inversals.append(Inversal(source=source, assignment=new_assignment))

        return inversals
