from .graphics import override_axes_methods
from .quib import override_numpy_functions
from .utils import ensure_only_run_once_globally


@ensure_only_run_once_globally
def override_all():
    """
    Overrides all modules (such as numpy and matplotlib) to support quibs
    """
    override_numpy_functions()
    override_axes_methods()
