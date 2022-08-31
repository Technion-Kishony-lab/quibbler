from pyquibbler.optional_packages.emulate_missing_packages import EMULATE_MISSING_PACKAGES

PACKAGE_NAME = 'ipywidgets'

if PACKAGE_NAME in EMULATE_MISSING_PACKAGES.val:
    raise ImportError

# noinspection PyPackageRequirements
import ipywidgets  # noqa: F401, E402

# noinspection PyPackageRequirements
from traitlets import TraitType  # noqa: F401, E402

from ipywidgets.widgets.widget_int import _BoundedIntRange  # noqa: F401, E402
from ipywidgets.widgets.widget_float import _BoundedFloatRange  # noqa: F401, E402
