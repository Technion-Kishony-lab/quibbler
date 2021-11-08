from __future__ import annotations
import contextlib
import functools

from pyquibbler.env import SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.exceptions import PyQuibblerException


class QuibCallFailedException(PyQuibblerException):

    def __init__(self, quibs_with_calls, exception):
        self.quibs_with_calls = quibs_with_calls
        self.exception = exception

    def __str__(self):
        quibs_formatted = ""
        for quib, call in self.quibs_with_calls[::-1]:
            file_info = f"File \"{quib.file_name}\", line {quib.line_no}" if quib.file_name else "Unnamed quib"
            quibs_formatted += "\n  " + file_info
            quibs_formatted += f"\n\t{repr(quib)} -------> {call}"
        last_quib, _ = self.quibs_with_calls[-1]
        return f"Failed to execute {last_quib}\n\n" \
               f"The following quibs were in the stack of the exception: {quibs_formatted} " \
               f"\n{type(self.exception).__name__}: {self.exception}"


@contextlib.contextmanager
def external_call_failed_exception_handling():
    """
    Use this context manager whenever running a quib's function that can fail user-wise
    (for example, whenever calling a np func or a user func)
    This should not be used around functions that can fail because pyquibbler internals themselves failed
    """
    try:
        yield
    except Exception as e:
        if SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS:
            raise QuibCallFailedException(quibs_with_calls=[], exception=e) from None
        raise


@contextlib.contextmanager
def add_quib_to_fail_trace_if_raises_quib_call_exception(quib, call: str, replace_last: bool = False):
    try:
        yield
    except QuibCallFailedException as e:
        new_quib_with_call = (quib, call)
        quibs_with_calls = e.quibs_with_calls
        if replace_last:
            previous_quib, _ = e.quibs_with_calls[-1]
            assert quib == previous_quib
            quibs_with_calls = quibs_with_calls[:-1]

        raise QuibCallFailedException(quibs_with_calls=[*quibs_with_calls, new_quib_with_call],
                                      exception=e.exception)


def raise_quib_call_exceptions_as_own(func):
    """
    Raise any quib call failed exceptions as though they were your own (so as to prevent long tracebacks)
    """
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except QuibCallFailedException as e:
            # We do this to clear the get_value_valid_at_path from traceback
            raise QuibCallFailedException(exception=e.exception, quibs_with_calls=e.quibs_with_calls) from None

    return _wrapper
