import numpy as np
from dataclasses import dataclass
from typing import Any, List, Optional, Union, Dict, Hashable

from .assignment import Assignment
from ..path.hashable import get_hashable_path
from pyquibbler.path.path_component import PathComponent
from .assignment_template import AssignmentTemplate
from ..path.data_accessing import deep_get, deep_assign_data_in_path


@dataclass
class AssignmentRemoval:
    path: List[PathComponent]


class Overrider:
    """
    Gathers function_definitions assignments performed on a quib in order to apply them on a quib value.
    """

    def __init__(self):
        self._paths_to_assignments: Dict[Hashable, Union[Assignment, AssignmentRemoval]] = {}
        self._active_assignment = None

    def _add_to_paths_to_assignments(self, assignment: Union[Assignment, AssignmentRemoval]):
        hashable_path = get_hashable_path(assignment.path)
        # We need to first remove and then add to make sure the new key value pair are now first in the dict
        if hashable_path in self._paths_to_assignments:
            self._paths_to_assignments.pop(hashable_path)
        self._paths_to_assignments[hashable_path] = assignment

    def add_assignment(self, assignment: Assignment):
        """
        Adds an override to the overrider - data[key] = value.
        """
        self._active_assignment = assignment
        self._add_to_paths_to_assignments(assignment)

    def remove_assignment(self, path: List[PathComponent]):
        """
        Remove function_definitions in a specific path.
        """
        if self._paths_to_assignments:
            assignment_removal = AssignmentRemoval(path)
            self.add_assignment(assignment_removal)
            return assignment_removal

    def undo_assignment(self,
                        previous_index: int,
                        previous_path: List[PathComponent],
                        assignment_to_return: Optional[Union[Assignment, AssignmentRemoval]]):
        """
        Undo an assignment, returning the overrider to the previous state before the assignment.
        Note that this is essentially different than simply adding an AssignmentRemoval ->
        if I do

        ```
        q = iquib(0)
        q.assign_value(1)
        q.assign_value(2)
        ```

        and then do remove_assignment, the value will go back to 0 (the original value).
        if I do undo_assignment, the value will go back to 1 (the previous value)
        """
        previous_assignment = self._paths_to_assignments.pop(get_hashable_path(previous_path))

        if assignment_to_return is not None:
            new_paths_with_assignments = list(self._paths_to_assignments.items())
            new_paths_with_assignments.insert(previous_index, (get_hashable_path(previous_path), assignment_to_return))
            self._paths_to_assignments = dict(new_paths_with_assignments)

        return previous_assignment

    def redo_assignment(self,
                        previous_index: int,
                        assignment_to_return: Union[Assignment, AssignmentRemoval]):
        """
        Redo an assignment that was undone- this is different than simply creating an assignment as it will put the
        assignment in the correct location in the dict
        """
        # There may not be anything where the assignment we removed was, so we pop with None so as not to raise
        self._paths_to_assignments.pop(get_hashable_path(assignment_to_return.path), None)

        new_paths_with_assignments = list(self._paths_to_assignments.items())
        new_paths_with_assignments.insert(previous_index, (get_hashable_path(assignment_to_return.path),
                                                           assignment_to_return))
        self._paths_to_assignments = dict(new_paths_with_assignments)

    def override(self, data: Any, assignment_template: Optional[AssignmentTemplate] = None):
        """
        Deep copies the argument and returns said data with applied overrides
        """
        from pyquibbler.quib.utils import deep_copy_without_quibs_or_graphics
        from pyquibbler import timer
        original_data = data
        with timer("quib_overriding"):
            data = deep_copy_without_quibs_or_graphics(data)
            for assignment in self._paths_to_assignments.values():
                if isinstance(assignment, AssignmentRemoval):
                    value = deep_get(original_data, assignment.path)
                    path = assignment.path
                else:
                    value = assignment.value if assignment_template is None \
                        else assignment_template.convert(assignment.value)
                    path = assignment.path

                data = deep_assign_data_in_path(data, path, value,
                                                raise_on_failure=assignment == self._active_assignment)

        self._active_assignment = None
        return data

    def fill_override_mask(self, false_mask):
        """
        Given a mask in the desired shape with all values set to False, update it so
        all cells in overridden indexes will be set to True.
        """
        mask = false_mask
        for assignment in self:
            path = assignment.path
            val = not isinstance(assignment, AssignmentRemoval)
            if path:
                if isinstance(path[-1].component, slice):
                    inner_data = deep_get(mask, path[:-1])
                    if not isinstance(inner_data, np.ndarray):
                        from pyquibbler.utilities.iterators import recursively_run_func_on_object
                        val = recursively_run_func_on_object(lambda x: val, inner_data)
                mask = deep_assign_data_in_path(mask, path, val)
            else:
                if val:
                    mask = np.ones(np.shape(assignment.value), dtype=bool)
                else:
                    mask = false_mask

        return mask

    def get(self, path: List[PathComponent], default_value: bool = None) -> Assignment:
        """
        Get the assignment at the given path
        """
        return self._paths_to_assignments.get(get_hashable_path(path), default_value)

    def __getitem__(self, item) -> Assignment:
        return list(self._paths_to_assignments.values())[item]

    def __repr__(self):
        return repr(self._paths_to_assignments.values())
