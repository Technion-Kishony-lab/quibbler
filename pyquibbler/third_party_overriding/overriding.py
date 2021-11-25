from .graphics_overriding import GRAPHICS_DEFINITIONS
from ..utils import ensure_only_run_once_globally


@ensure_only_run_once_globally
def override_third_party_funcs():
    for definition in GRAPHICS_DEFINITIONS:
        definition.override()
