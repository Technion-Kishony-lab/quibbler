import copy
import pathlib
import pickle

import numpy as np
from typing import Any, Optional, Dict, Hashable, List, Union

from dataclasses import dataclass, field
from .assignment import Assignment, AssignmentWithTolerance, convert_assignment_with_tolerance_to_pretty_assignment
from .exceptions import NoAssignmentFoundAtPathException
from ..path.hashable import get_hashable_path
from pyquibbler.path.path_component import Path, Paths, PathComponent
from .assignment_template import AssignmentTemplate
from ..path.data_accessing import deep_get, deep_assign_data_in_path
from .default_value import default

from pyquibbler.quib.external_call_failed_exception_handling import external_call_failed_exception_handling


@dataclass
class GetReference:
    assignments: List[Assignment] = field(default_factory=list)
    current_path: Path = field(default_factory=list)

    def _add_key_to_path(self, key):
        self.current_path.append(PathComponent(None, key))

    def __getitem__(self, key):
        self._add_key_to_path(key)
        return self

    def __setitem__(self, key, value):
        self._add_key_to_path(key)
        self.assign(value)

    def assign(self, value):
        self.assignments.append(Assignment(value, self.current_path))
        self.current_path = []


PathsToAssignments = Dict[Hashable, Assignment]


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

    def _add_to_paths_to_assignments(self, assignment: Assignment):
        hashable_path = get_hashable_path(assignment.path)
        # We need to first remove and then add to make sure the new key value pair are now first in the dict
        if hashable_path in self._paths_to_assignments:
            self._paths_to_assignments.pop(hashable_path)
        self._paths_to_assignments[hashable_path] = assignment

    def add_assignment(self, assignment: Union[Assignment, AssignmentWithTolerance]):
        """
        Adds an override to the overrider - data[key] = value.
        """
        assignment = copy.deepcopy(assignment)
        assignment.remove_class_from_path()
        if isinstance(assignment, AssignmentWithTolerance):
            assignment = convert_assignment_with_tolerance_to_pretty_assignment(assignment)
        self._active_assignment = assignment
        self._add_to_paths_to_assignments(assignment)

    def pop_assignment_at_path(self, path: Path, raise_on_not_found: bool = True):
        hashable_path = get_hashable_path(path)
        if raise_on_not_found and hashable_path not in self._paths_to_assignments:
            raise NoAssignmentFoundAtPathException(path=path)
        return self._paths_to_assignments.pop(hashable_path, None)

    def pop_assignment_at_index(self, index: int):
        new_paths_with_assignments = list(self._paths_to_assignments.items())
        _, assignment = new_paths_with_assignments.pop(index)
        self._paths_to_assignments = dict(new_paths_with_assignments)
        return assignment

    def insert_assignment_at_index(self, assignment: Assignment, index: int):
        hashable_path = get_hashable_path(assignment.path)
        new_paths_with_assignments = list(self._paths_to_assignments.items())
        new_paths_with_assignments.insert(index, (hashable_path, assignment))

        # We need to remove any assignments with the same path that came before this index so we don't accidentally
        # use those (previous) assignments when running `dict` on the list
        for i, (path, assignment) in enumerate(new_paths_with_assignments[:index][:]):
            if hashable_path == path:
                new_paths_with_assignments.pop(i)

        from pyquibbler.logger import logger
        logger.info(f"New paths with assignments {new_paths_with_assignments}")
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
                if assignment.is_default():
                    value = deep_get(original_data, assignment.path)
                else:
                    value = assignment.value
                with external_call_failed_exception_handling():
                    data = deep_assign_data_in_path(data, assignment.path, value,
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
            val = assignment.value is not default
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
            f.write(self.get_pretty_repr())

    def load_from_assignment_text(self, assignment_text: str):
        self.clear_assignments()
        try:
            quib = GetReference()
            exec(assignment_text, {'quib': quib, 'array': np.array, 'default': default})
            for assignment in quib.assignments:
                self.add_assignment(assignment)
        except Exception:
            from ..quib.exceptions import CannotLoadAssignmentsFromTextException
            raise CannotLoadAssignmentsFromTextException(assignment_text) from None
        return [[]]

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

    def get_pretty_repr(self, name: str = None):
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
        return self.get_pretty_repr()
