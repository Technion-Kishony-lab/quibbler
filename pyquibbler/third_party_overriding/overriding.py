from pyquibbler.third_party_overriding.graphics.graphics_overriding import GRAPHICS_DEFINITIONS
from pyquibbler.third_party_overriding.graphics.widgets.switch_widgets_with_q_widgets import switch_widgets_to_quib_supporting_widgets
from pyquibbler.third_party_overriding.graphics.widgets.widgets_overriding import override_widgets_with_quib_creators
from ..utils import ensure_only_run_once_globally


@ensure_only_run_once_globally
def override_third_party_funcs():
    switch_widgets_to_quib_supporting_widgets()
    override_widgets_with_quib_creators()
    for definition in GRAPHICS_DEFINITIONS:
        definition.override()
