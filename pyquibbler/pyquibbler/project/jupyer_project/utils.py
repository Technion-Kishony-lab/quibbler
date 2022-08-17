import re
import socket

from pyquibbler import Quib, Assignment
from pyquibbler.assignment import Overrider
from pyquibbler.env import REPR_WITH_OVERRIDES
from pyquibbler.logger import logger


def find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))            # Bind to a free port provided by the host.
        return s.getsockname()[1]  # Return the port number assigned.


def is_within_jupyter_lab():
    try:
        # noinspection PyPackageRequirements
        from IPython import get_ipython

        # noinspection PyPackageRequirements
        from ipykernel.comm import Comm  # noqa: F401

        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except (NameError, ImportError):
        return False      # Probably standard Python interpreter


def create_raw_overrides_from_overrider(overrider: Overrider):
    if overrider.can_save_to_txt():
        return [{
            'left': assignment.get_pretty_path(),
            'right': assignment.get_pretty_value()
        } for assignment in overrider._paths_to_assignments.values()]

    return None


def get_serialized_quib(quib: Quib):
    with REPR_WITH_OVERRIDES.temporary_set(False):
        repr_ = repr(quib)

    return {
        "id": id(quib),
        "name": quib.name,
        "repr": repr_,
        "overrides": create_raw_overrides_from_overrider(quib.handler.overrider),
        "synced": quib.handler.file_syncer.is_synced
    }
