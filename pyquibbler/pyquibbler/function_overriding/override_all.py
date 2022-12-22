from typing import List, Dict

from pyquibbler.project.jupyer_project.jupyter_project import create_jupyter_project_if_in_jupyter_lab
from pyquibbler.function_definitions import add_definition_for_function
from pyquibbler.utilities.input_validation_utils import validate_user_input
from pyquibbler.utilities.warning_messages import no_header_warn
from pyquibbler.env import DRAGGABLE_PLOTS_BY_DEFAULT, SHOW_QUIBS_AS_WIDGETS_IN_JUPYTER_LAB

from .attribute_override import AttributeOverride
from .defintion_without_override.python_functions import create_definitions_for_python_functions
from .exceptionhook import override_jupyterlab_excepthook
from .function_override import FuncOverride
from .is_initiated import IS_QUIBBLER_INITIATED
from .third_party_overriding.ipywidgets.overrides import override_ipywidgets_if_installed
from .third_party_overriding.non_quib_overrides import override_axes_methods, switch_widgets_to_quib_supporting_widgets
from .quib_overrides.operators.overrides import create_operator_overrides
from .quib_overrides.quib_methods import create_quib_method_overrides
from .third_party_overriding.numpy.overrides import create_numpy_overrides
from .third_party_overriding.matplotlib.overrides import create_graphics_overrides
from .third_party_overriding.numpy.quiby_attributes import get_numpy_attributes_to_attribute_overrides, \
    get_numpy_methods_to_method_overrides
from ..project.jupyer_project.utils import is_within_colab

ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES: Dict[str, AttributeOverride] = {}


@validate_user_input(draggable_plots=bool, show_quibs_as_widgets=bool, jupyterlab_extension=bool)
def initialize_quibbler(draggable_plots: bool = True,
                        show_quibs_as_widgets: bool = True,
                        jupyterlab_extension: bool = True):
    """
    Initialize Quibbler to allow functions to work on quibs

    Initiate quibbler and override all relevant functions and operators in NumPy, Matplotlib,
    and ipywidgets to support Quibs.

    Parameters
    ----------
    draggable_plots: bool, default True
        Indicates whether plots created by matplotlib `plot` and `scatter`
        are mouse draggable by default (namely, allowing graphics-based assignments).

        When set to `True`, plots are automatically draggable. Indicate `picker=False`
        in a `plot` or `scatter` function call to prevent dragging for a specific plot.

        When set to `False`, plots are not draggable, unless `picker=True` is
        specified in the `plot` or `scatter` function calls.

    show_quibs_as_widgets: bool, default True
        Indicates whether to display quibs as interactive widgets within Jupyter Lab.
        When set to False, quibs can still be displayed as widgets using the quib's `display()` method.
        (Note that `show_quibs_as_widgets` is only applicable within Jupyter Lab).

    jupyterlab_extension: bool, default True
        Indicates whether to connect with the pyquibbler_labextension to allow save/load of quibs to the
        Jupyter notebook.

    See Also
    --------
    quiby, is_quiby, q, list_quiby_funcs, Project, Quib.display

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
    ``initialize_quibbler`` need only be called once at the beginning of the script,
    after pyquibbler is imported.
    Additional calls, though, are harmless and can even be useful as a means to re-specify
    `draggable_plots` and `show_quibs_as_widgets`.
    """

    DRAGGABLE_PLOTS_BY_DEFAULT.set(draggable_plots)
    SHOW_QUIBS_AS_WIDGETS_IN_JUPYTER_LAB.set(show_quibs_as_widgets)

    if IS_QUIBBLER_INITIATED:
        return

    within_jupyterlab = jupyterlab_extension and create_jupyter_project_if_in_jupyter_lab()

    func_definitions = create_definitions_for_python_functions()
    for func, func_definition in func_definitions.items():
        add_definition_for_function(
            func=func,
            func_definition=func_definition,
            module_or_cls=None,
        )

    switch_widgets_to_quib_supporting_widgets()

    override_axes_methods()

    ipywidgets_installed = override_ipywidgets_if_installed()

    if not ipywidgets_installed and within_jupyterlab:
        no_header_warn('It is not a requirement, but do consider installing ipywidgets to '
                       'further enhance pyquibbler interactivity in Jupyter lab.\n')

    if is_within_colab():
        no_header_warn('To learn how to set up Quibbler to work within colab, see here:\n'
                       'https://colab.research.google.com/drive/1kZ3m8DdImiS0FJv8_VOZO8VuQdPkCBg8?usp=sharing\n'
                       '\n'
                       'Note though that Quibbler is not well optimized for work within colab\n'
                       'and any interactive graphics will be very slow.\n')

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

    ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES.update(get_numpy_attributes_to_attribute_overrides())
    ATTRIBUTES_TO_ATTRIBUTE_OVERRIDES.update(get_numpy_methods_to_method_overrides())

    if within_jupyterlab:
        override_jupyterlab_excepthook()

    IS_QUIBBLER_INITIATED.set(True)
