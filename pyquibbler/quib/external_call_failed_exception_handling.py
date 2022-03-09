from __future__ import annotations
import contextlib
import functools
import sys
import traceback

from varname.utils import cached_getmodule

from pyquibbler.env import SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS
from pyquibbler.exceptions import PyQuibblerException


class ExternalCallFailedException(PyQuibblerException):

    def __init__(self, quibs_with_calls, exception, tb):
        self.quibs_with_calls = quibs_with_calls
        self.exception = exception
        self.traceback = tb

    def __str__(self):
        quibs_formatted = ""
        for quib, call in self.quibs_with_calls[::-1]:
            file_info = f"File \"{quib.file_name}\", line {quib.line_no}" if quib.file_name else "Unnamed quib"
            quibs_formatted += "\n  " + file_info
            quibs_formatted += f"\n\t{repr(quib)} -> {call} "

        last_quib, _ = self.quibs_with_calls[-1]
        return f"Failed to execute {last_quib}\n\n" \
               f"The following quibs were in the stack of the exception: {quibs_formatted} " \
               f"\n\n{self.traceback}"


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
        # get traceback outside of pyquibbler
        type_, exc, tb = sys.exc_info()
        while tb is not None and cached_getmodule(tb.tb_frame.f_code) is not None \
                and cached_getmodule(tb.tb_frame.f_code).__name__.startswith("pyquibbler"):
            tb = tb.tb_next

        if SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS:
            if tb is None:
                formatted_tb = ''.join(traceback.format_exception_only(type_, value=exc))
            else:
                traceback_lines = traceback.format_exception(type_, exc, tb)
                formatted_tb = ''.join(traceback_lines)

            raise ExternalCallFailedException(quibs_with_calls=[],
                                              exception=e,
                                              tb=formatted_tb) from None
        raise


@contextlib.contextmanager
def add_quib_to_fail_trace_if_raises_quib_call_exception(quib, call: str, replace_last: bool = False):
    try:
        yield
    except ExternalCallFailedException as e:
        new_quib_with_call = (quib, call)
        quibs_with_calls = e.quibs_with_calls
        if replace_last:
            previous_quib, _ = e.quibs_with_calls[-1]
            assert quib == previous_quib
            quibs_with_calls = quibs_with_calls[:-1]

        raise ExternalCallFailedException(quibs_with_calls=[*quibs_with_calls, new_quib_with_call],
                                          exception=e.exception, tb=e.traceback)


def raise_quib_call_exceptions_as_own(func):
    """
    Raise any quib call failed exceptions as though they were your own (so as to prevent long tracebacks)
    """
    @functools.wraps(func)
    def _wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ExternalCallFailedException as e:
            # We want to remove any context
            raise ExternalCallFailedException(exception=e.exception,
                                              quibs_with_calls=e.quibs_with_calls,
                                              tb=e.traceback) from None

    return _wrapper
