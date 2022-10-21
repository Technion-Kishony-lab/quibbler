from __future__ import annotations

from dataclasses import dataclass, field

from typing import List, Optional, Iterable, Any

from .default_value import default, Default
from .assignment import Assignment

from pyquibbler.path import Path, PathComponent
from pyquibbler.utilities.numpy_original_functions import np_array
from pyquibbler.utilities.iterators import recursively_run_func_on_object
from .exceptions import CannotConvertTextToAssignmentsException, CannotConvertAssignmentsToTextException


ASSIGNMENT_VALUE_TEXT_DICT = {'array': np_array, 'default': default}


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


def convert_assignments_to_executable_text(
        assignments: Iterable[Assignment], name: Optional[str] = None, raise_if_not_reversible: bool = False) -> str:
    """
    Convert list of Assignments to text.
    """
    name = 'quib' if name is None else name
    pretty = ''
    for assignment in assignments:
        if raise_if_not_reversible:
            if not is_saveable_as_txt([cmp.component for cmp in assignment.path]) \
                    or not is_saveable_as_txt(assignment.value):
                raise CannotConvertAssignmentsToTextException()
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
