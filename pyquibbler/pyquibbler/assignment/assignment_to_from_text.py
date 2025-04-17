from __future__ import annotations

from dataclasses import dataclass, field

from typing import List, Optional, Iterable, Any, Dict

import numpy as np

from .default_value import default, Default
from .assignment import Assignment

from pyquibbler.path import Path, PathComponent
from pyquibbler.utilities.numpy_original_functions import np_array
from pyquibbler.utilities.iterators import recursively_run_func_on_object
from .exceptions import CannotConvertTextToAssignmentsException, CannotConvertAssignmentsToTextException

ASSIGNMENT_VALUE_TEXT_DICT = {'array': np_array, 'default': default, 'np': np}


def to_json_compatible(obj):
    """
    Recursively converts Python objects into a JSON‑serializable format.
    """
    if isinstance(obj, float) and (
            np.isnan(obj) or np.isinf(obj) or np.isclose(obj, np.round(obj))):
        # Handle NaN, inf, and roundable floats (otherwise Jupyetr's JSON of 5.0 is 5)
        return repr(obj)
    elif isinstance(obj, (int, float, bool)) or obj is None:
        return obj
    elif isinstance(obj, dict):
        return {repr(k): to_json_compatible(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [to_json_compatible(item) for item in obj]
    else:
        return repr(obj)


def from_json_compatible(obj):
    """
    Converts a JSON compatible object back to its original Python type.
    """
    if isinstance(obj, dict):
        return {from_json_compatible(k): from_json_compatible(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [from_json_compatible(item) for item in obj]
    elif isinstance(obj, str):
        return eval(obj, ASSIGNMENT_VALUE_TEXT_DICT)
    else:
        return obj


@dataclass
class GetReference:
    """
    A dummy object that records a list of assignments made to it.

    Mimicking a quib, a GetReference object accepts deep assignments
    as well as the .assign(value) syntax.
    """
    assignments: List[Assignment] = field(default_factory=list)
    current_path: Path = field(default_factory=list)

    def _add_key_to_path(self, key):
        self.current_path.append(PathComponent(key))

    def __getitem__(self, key):
        self._add_key_to_path(key)
        return self

    def __setitem__(self, key, value):
        self._add_key_to_path(key)
        self.assign(value)

    def assign(self, value):
        self.assignments.append(Assignment(value, self.current_path))
        self.current_path = []


def is_saveable_as_txt(val: Any) -> bool:
    all_ok = True

    def set_false_if_repr_is_not_invertible(v):
        from numpy import ndarray, int64, int32, bool_
        nonlocal all_ok
        all_ok &= isinstance(v, (Default, bool, str, int, float, ndarray, slice, type(None), int64, int32, bool_))

    # TODO: for dicts we need to check also that the keys are saveable
    recursively_run_func_on_object(func=set_false_if_repr_is_not_invertible, obj=val)
    return all_ok


def convert_executable_text_to_assignments(assignment_text: str) -> List[Assignment]:
    """
    Convert text with multiple assignment statements into a list of assignments.
    The text should refer to an object named 'quib'.

    For example, assignment_text may include lines like these:
    quib[1] = 7
    quib[1,:]['name'] = 'Joe'
    quib.assign(972)
    """
    try:
        quib = GetReference()
        exec(assignment_text, {'quib': quib, **ASSIGNMENT_VALUE_TEXT_DICT})
        return quib.assignments
    except Exception:
        raise CannotConvertTextToAssignmentsException(assignment_text) from None


def raise_if_assignment_is_not_saveable(assignment: Assignment):
    if not is_saveable_as_txt([cmp.component for cmp in assignment.path]) \
            or not is_saveable_as_txt(assignment.value):
        raise CannotConvertAssignmentsToTextException()


def convert_assignments_to_executable_text(
        assignments: Iterable[Assignment], name: Optional[str] = None, raise_if_not_saveable: bool = False) -> str:
    """
    Convert list of Assignments to text.
    """
    name = 'quib' if name is None else name
    pretty = ''
    for assignment in assignments:
        if raise_if_not_saveable:
            raise_if_assignment_is_not_saveable(assignment)
        pretty_value = assignment.get_pretty_value()
        pretty += '\n' + name
        if assignment.path:
            pretty += assignment.get_pretty_path()
            pretty += ' = ' + pretty_value
        else:
            pretty += '.assign(' + pretty_value + ')'
    pretty = pretty[1:] if pretty else pretty  # remove '\n'
    return pretty


def convert_simplified_text_to_assignment(assignment_text: str) -> Assignment:
    """
    Convert an assignment text into an Assignment.

    Accepts three forms of text:

    'value' -> Assignment(path=[], value), like quib.assign(value)

    '= value' -> Assignment(path=[], value), like quib.assign(value)

    '[comp0][comp1]...[compN] = value' -> Assignment(path=[comp0, comp1, ..., compN], value)
    """
    assignment_text = assignment_text.strip()

    if assignment_text.startswith('='):
        # '= value'
        assignment_text = f'quib.assign({assignment_text[1:]})'
    else:
        try:
            eval(assignment_text, ASSIGNMENT_VALUE_TEXT_DICT)  # triggers exception if text is an assignment statement
            # 'value'
            assignment_text = f'quib.assign({assignment_text})'
        except Exception:
            # 'path = value'
            assignment_text = f'quib{assignment_text}'

    assignments = convert_executable_text_to_assignments(assignment_text)

    if len(assignments) != 1:
        raise CannotConvertTextToAssignmentsException(assignment_text) from None

    return assignments[0]


def convert_assignment_to_simplified_text(assignment: Assignment) -> str:
    """
    Convert an Assignment to text.

    full, no-path assignment:
    Assignment(path=[], value)  ->  '= value'

    at-path assignment:
    Assignment(path=[comp0, comp1, ..., compN], value) -> '[comp0][comp1]...[compN] = value'
    """
    if len(assignment.path) == 0:
        return '= ' + assignment.get_pretty_value()

    return assignment.get_pretty_path() + ' = ' + assignment.get_pretty_value()


def convert_assignments_to_json_compatible_dict(
        assignments: List[Assignment], raise_if_not_saveable: bool = False) -> Dict[str, Any]:
    """
    Convert a list of assignments to a dict of str of the path to str of the value.
    Use ordered dict
    """
    paths_to_values = {}
    for assignment in assignments:
        if raise_if_not_saveable:
            raise_if_assignment_is_not_saveable(assignment)
        paths_to_values[assignment.get_pretty_path()] = to_json_compatible(assignment.get_de_np_value())
    return paths_to_values


def convert_json_compatible_dict_to_assignments(
        assignment_dict: Dict[str, Any]) -> List[Assignment]:
    """
    Convert a dict of str of the path to str of the value to a list of assignments.
    Use convert_simplified_text_to_assignment.
    """
    return [convert_simplified_text_to_assignment(f'{path_str} = {from_json_compatible(value)}')
            for path_str, value in assignment_dict.items()]
