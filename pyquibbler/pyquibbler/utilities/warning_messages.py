import contextlib
import warnings
from typing import Tuple, Optional, Union


def _no_header_formatwarning(msg, *args, **kwargs):
    return str(msg) + '\n'


@contextlib.contextmanager
def _no_header_warning():
    original_formatwarning = warnings.formatwarning
    warnings.formatwarning = _no_header_formatwarning
    yield
    warnings.formatwarning = original_formatwarning


def no_header_warn(msg: Union[str, Tuple[str, ...]], add_frame: bool = False, once_only: bool = False):
    """
    Issue a bare warning message.
    Do not include in the warning a header with the file path.
    """
    if isinstance(msg, str):
        msg = (msg, )
    if add_frame:
        msg = create_frame(msg)
    msg = '\n'.join(msg)
    with _no_header_warning():
        if once_only:
            warnings.warn(msg)
        else:
            warnings.showwarning(msg, category=UserWarning, filename=None, lineno=None)


def create_frame(message_lines: Tuple[str, ...], width: Optional[int] = None):
    if width is None:
        max_length = max(len(line) for line in message_lines)
        width = max_length + 4

    return (
        '-' * width,
        *('| ' + line + ' ' * (width - len(line) - 3) + '|' for line in message_lines),
        '-' * width,
    )
