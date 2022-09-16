from typing import List

from pyquibbler.utilities.decorators import ensure_only_run_once_globally
from pyquibbler.project.jupyer_project.jupyter_project import create_jupyter_project_if_in_jupyter_lab
from pyquibbler.function_definitions import add_definition_for_function
from .defintion_without_override.python_functions import create_definitions_for_python_functions
from .exceptionhook import override_jupyterlab_excepthook
from .function_override import FuncOverride
from .is_initiated import IS_QUIBBLER_INITIATED
from .third_party_overriding.ipywidgets.overrides import override_ipywidgets_if_installed
from .third_party_overriding.non_quib_overrides import override_axes_methods, switch_widgets_to_quib_supporting_widgets
from .quib_overrides.operators.overrides import create_operator_overrides
from .quib_overrides.quib_methods import create_quib_method_overrides
from .third_party_overriding.numpy.overrides import create_numpy_overrides
from .third_party_overriding.graphics.overrides import create_graphics_overrides
from ..utilities.warning_messages import no_header_warn


@ensure_only_run_once_globally
def initialize_quibbler():
    """
    Initialize Quibbler to allow functions to work on quibs

    Override all relevant functions, both operators and third party, to support Quibs.
    Need to run once *before* importing from NumPy or Matplotlib.

    See Also
    --------
    quiby, is_quiby, q, list_quiby_funcs, Project

    Examples
    --------
    >>> import numpy as np
    >>> from pyquibbler import initialize_quibbler, is_quiby
    >>> is_quiby(np.sin)
    False
    >>> initialize_quibbler()
    >>> is_quiby(np.sin)
    True

    ``initialize_quibbler`` must be called before importing *from* NumPy or Matplotlib.
    It will not work on functions already imported from these packages:

    >>> from numpy import sin
    >>> from pyquibbler import initialize_quibbler, is_quiby
    >>> is_quiby(sin)
    False
    >>> initialize_quibbler()
    >>> is_quiby(sin)
    False

    Note
    ----
    Only need to run ``initialize_quibbler`` once. Additional calls are gracefully ignored.
    """

    within_jupyterlab = create_jupyter_project_if_in_jupyter_lab()

    function_definitions = create_definitions_for_python_functions()
    for func_definition in function_definitions:
        add_definition_for_function(
            func=func_definition.func,
            func_definition=func_definition,
            module_or_cls=None,
        )

    switch_widgets_to_quib_supporting_widgets()

    override_axes_methods()

    ipywidgets_installed = override_ipywidgets_if_installed()

    if not ipywidgets_installed and within_jupyterlab:
        no_header_warn('It is not a requirement, but do consider installing ipywidgets to '
                       'further enhance pyquibbler interactivity in Jupyter lab.\n')

    function_overrides: List[FuncOverride] = [*create_operator_overrides(),
                                              *create_graphics_overrides(),
                                              *create_numpy_overrides(),
                                              *create_quib_method_overrides()]
    for func_override in function_overrides:
        maybe_create_quib = func_override.override()
        add_definition_for_function(
            func=func_override.original_func,
            func_definition=func_override.func_definition,
            module_or_cls=func_override.module_or_cls,
            func_name=func_override.func_name,
            quib_creating_func=maybe_create_quib)

    if within_jupyterlab:
        override_jupyterlab_excepthook()

    IS_QUIBBLER_INITIATED.set(True)
