import contextlib
import warnings


def _no_header_formatwarning(msg, *args, **kwargs):
    return str(msg) + '\n'


@contextlib.contextmanager
def _no_header_warning():
    original_formatwarning = warnings.formatwarning
    warnings.formatwarning = _no_header_formatwarning
    yield
    warnings.formatwarning = original_formatwarning


def no_header_warn(msg: str):
    """
    Issue a bare warning message.
    Do not include in the warning a header with the file path.
    """
    with _no_header_warning():
        warnings.warn(msg)
