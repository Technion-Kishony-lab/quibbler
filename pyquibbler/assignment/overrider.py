import copy
import pathlib
import pickle
from unittest import mock

import numpy as np
from dataclasses import dataclass
from typing import Any, Optional, Union, Dict, Hashable, List

from .assignment import Assignment
from ..logger import logger
from ..path.hashable import get_hashable_path
from pyquibbler.path.path_component import Path, Paths
from .assignment_template import AssignmentTemplate
from ..path.data_accessing import deep_get, deep_assign_data_in_path

from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling


@dataclass
class AssignmentRemoval:
    path: Path


PathsToAssignments = Dict[Hashable, Union[Assignment, AssignmentRemoval]]


class Overrider:
    """
    Gathers function_definitions assignments performed on a quib in order to apply them on a quib value.
    """

    def __init__(self):
        self._paths_to_assignments: PathsToAssignments = {}
        self._active_assignment = None

    def clear_assignments(self) -> Paths:
        return self.replace_assignments({})

    def replace_assignments(self, new_paths_to_assignments: PathsToAssignments) -> Paths:
        """
        replace assignment list and return the changed paths
        """
        self._paths_to_assignments = new_paths_to_assignments
        self._active_assignment = None
        # TODO: invalidate only the changed paths
        return [[]]

    def _add_to_paths_to_assignments(self, assignment: Union[Assignment, AssignmentRemoval]):
        hashable_path = get_hashable_path(assignment.path)
        # We need to first remove and then add to make sure the new key value pair are now first in the dict
        if hashable_path in self._paths_to_assignments:
            self._paths_to_assignments.pop(hashable_path)
        self._paths_to_assignments[hashable_path] = assignment

    def add_assignment(self, assignment: Union[Assignment, AssignmentRemoval]):
        """
        Adds an override to the overrider - data[key] = value.
        """
        assignment_without_indexed_cls = copy.deepcopy(assignment)
        for component in assignment_without_indexed_cls.path:
            component.indexed_cls = None

        self._active_assignment = assignment_without_indexed_cls
        self._add_to_paths_to_assignments(assignment_without_indexed_cls)

    def remove_assignment(self, path: Path):
        """
        Remove function_definitions in a specific path.
        """
        if self._paths_to_assignments:
            assignment_removal = AssignmentRemoval(path)
            self.add_assignment(assignment_removal)
            return assignment_removal

    def undo_assignment(self,
                        previous_index: int,
                        previous_path: Path,
                        assignment_to_return: Optional[Union[Assignment, AssignmentRemoval]]):
        """
        Undo an assignment, returning the overrider to the previous state before the assignment.
        Note that this is essentially different than simply adding an AssignmentRemoval ->
        if I do
        ```
        q = iquib(0)
        q.assign(1)
        q.assign(2)
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
                with external_call_failed_exception_handling():
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

    def get(self, path: Path, default_value: bool = None) -> Assignment:
        """
        Get the assignment at the given path
        """
        return self._paths_to_assignments.get(get_hashable_path(path), default_value)

    def __getitem__(self, item) -> Assignment:
        return list(self._paths_to_assignments.values())[item]

    def __len__(self):
        return len(self._paths_to_assignments)

    """
    save/load
    """

    def save_as_binary(self, file: pathlib.Path):
        with open(file, 'wb') as f:
            pickle.dump(self._paths_to_assignments, f)

    def load_from_binary(self, file: pathlib.Path) -> List[Path]:
        with open(file, 'rb') as f:
            return self.replace_assignments(pickle.load(f))

    def can_save_to_txt(self) -> bool:
        from pyquibbler.quib.utils.miscellaneous import is_saveable_as_txt
        for assignment in self._paths_to_assignments.values():
            if not is_saveable_as_txt([cmp.component for cmp in assignment.path]) \
                    or isinstance(assignment, Assignment) and not is_saveable_as_txt(assignment.value):
                return False
        return True

    def save_as_txt(self, file: pathlib.Path):
        from pyquibbler.quib.exceptions import CannotSaveAssignmentsAsTextException
        if not self.can_save_to_txt():
            raise CannotSaveAssignmentsAsTextException()
        with open(file, "wt") as f:
            f.write(self.pretty_repr())

    def load_from_assignment_text(self, assignment_text: str):
        from pyquibbler import iquib
        from ..quib.exceptions import CannotLoadAssignmentsFromTextException
        # TODO: We are using exec. This is very simple, but obviously highly risky.
        #  Will be good to replace with a dedicated parser.
        quib = iquib(None)
        try:
            exec(assignment_text, {
                'array': np.array,
                'quib': quib
            })
        except Exception:
            raise
            # raise CannotLoadAssignmentsFromTextException(assignment_text) from None
        return self.replace_assignments(quib.handler.overrider._paths_to_assignments)

    def load_from_txt(self, file: pathlib.Path):
        """
        load assignments from text file.
        """
        with open(file, mode='r') as f:
            assignment_text_commands = f.read()
        return self.load_from_assignment_text(assignment_text_commands)

    """
    repr
    """

    def pretty_repr(self, name: str = None):
        name = 'quib' if name is None else name
        from ..quib.pretty_converters.pretty_convert import getitem_converter
        pretty = ''
        for assignment in self._paths_to_assignments.values():
            pretty_value = repr(assignment.value) if isinstance(assignment, Assignment) else 'default'
            pretty += '\n' + name
            if assignment.path:
                pretty += ''.join([str(getitem_converter(None, ('', cmp.component))) for cmp in assignment.path])
                pretty += ' = ' + pretty_value
            else:
                pretty += '.assign(' + pretty_value + ')'
        pretty = pretty[1:] if pretty else pretty
        return pretty

    def __repr__(self):
        return self.pretty_repr()
