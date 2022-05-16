import re
import socket

from pyquibbler import Quib
from pyquibbler.logger import logger


def find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))            # Bind to a free port provided by the host.
        return s.getsockname()[1]  # Return the port number assigned.


def is_within_jupyter_lab():
    try:
        from IPython import get_ipython
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except (NameError, ImportError):
        return False      # Probably standard Python interpreter


def create_raw_override_from_override_line(line: str):
    if ' = ' in line:
        left, right = line.split(" = ")
    else:
        left = "quib"
        right = re.match(r".*\((.*?)\)", line).groups()[0]
    return {
        'left': left,
        'right': right
    }


def create_raw_overrides_from_override_repr(overrider_repr):
    return [create_raw_override_from_override_line(line) for line in overrider_repr.strip().split("\n")]


def get_serialized_quib(quib: Quib):
    overrider = quib.handler.overrider
    overrider_repr = overrider.pretty_repr() if overrider.can_save_to_txt() else None
    if overrider_repr is None:
        raw_overrides = None
    elif overrider_repr.strip() == "":
        raw_overrides = []
    else:
        raw_overrides = create_raw_overrides_from_override_repr(overrider_repr)
    logger.info("Sending {} for {}".format(overrider_repr, quib))
    return {
        "id": id(quib),
        "name": quib.name,
        "overrides": raw_overrides,
        "synced": quib.handler.file_syncer.is_synced
    }
