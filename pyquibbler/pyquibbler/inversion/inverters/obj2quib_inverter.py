from pyquibbler.assignment import Assignment
from pyquibbler.inversion.inverter import Inverter
from pyquibbler.path import split_path_at_end_of_object, deep_get
from pyquibbler.path_translation.types import Inversal, Source
from pyquibbler.utilities.iterators import get_paths_for_objects_of_type


class Obj2QuibInverter(Inverter):

    def get_inversals(self):
        assignment_path = self._assignment.path
        path_within_object, remaining_path, obj = split_path_at_end_of_object(self._func_call.args[0],
                                                                              path=assignment_path)

        if isinstance(obj, Source):
            # the assignment refers to, or within, a source
            return [
                Inversal(
                    assignment=Assignment(
                        path=remaining_path,
                        value=self._assignment.value),
                    source=obj)
                   ]

        # the assignment refers to a non-source object. all sources within this object are assigned full value
        # based on this path within the object, referring to the result with assignment.
        result = self._get_result_with_assignment_set()
        paths_to_sources_within_assignment_path = get_paths_for_objects_of_type(obj, Source)
        inversals = []
        for path_to_source_within_assignment_path in paths_to_sources_within_assignment_path:
            source = deep_get(obj, path_to_source_within_assignment_path)
            path_in_result = assignment_path + path_to_source_within_assignment_path
            inversals.append(
                Inversal(
                    assignment=Assignment(
                        path=[],
                        value=deep_get(result, path_in_result)
                    ),
                    source=source
                )

            )
        return inversals
