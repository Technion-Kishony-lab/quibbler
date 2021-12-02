from .graphics_overriding import GRAPHICS_DEFINITIONS
from .widgets_overriding import switch_widgets_to_quib_supporting_widgets, override_widgets_with_quib_creators
from ..utils import ensure_only_run_once_globally


@ensure_only_run_once_globally
def override_third_party_funcs():
    switch_widgets_to_quib_supporting_widgets()
    override_widgets_with_quib_creators()
    for definition in GRAPHICS_DEFINITIONS:
        definition.override()
