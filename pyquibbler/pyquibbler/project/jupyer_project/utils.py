import socket
import sys


def find_free_port():
    with socket.socket() as s:
        s.bind(('', 0))            # Bind to a free port provided by the host.
        return s.getsockname()[1]  # Return the port number assigned.


def is_within_jupyter_lab() -> bool:
    try:
        from pyquibbler.optional_packages.get_IPython import get_ipython, Comm   # noqa: F401
        shell = get_ipython().__class__.__name__
        if shell == 'ZMQInteractiveShell':
            return True   # Jupyter notebook or qtconsole
        elif shell == 'TerminalInteractiveShell':
            return False  # Terminal running IPython
        else:
            return False  # Other type (?)
    except (NameError, ImportError):
        return False      # Probably standard Python interpreter


def is_within_colab() -> bool:
    return 'google.colab' in sys.modules
