from dataclasses import dataclass
from typing import Optional, Union

from pyquibbler.assignment import AssignmentToQuib, create_assignment
from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
from pyquibbler.graphics.widgets import QSlider, QRangeSlider
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.widget_call import WidgetQuibFuncCall
from pyquibbler.quib.quib import Quib


@dataclass
class SliderQuibFuncCall(WidgetQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        return 'valinit'

    def _on_change_slider(self, new_value, widget: Union[QSlider, QRangeSlider]):
        val = self.func_args_kwargs.get('valinit')
        if widget.valstep is None and GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val is not None:
            tolerance = (widget.valmax - widget.valmin) / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val
        else:
            tolerance = None

        if isinstance(val, Quib):
            self._inverse_assign(val, [], new_value, tolerance=tolerance, on_drag=True)
        elif len(val) == 2:
            quib_changes = list()
            for index, val_item in enumerate(val):
                if isinstance(val_item, Quib):
                    quib_changes.append(AssignmentToQuib(
                        quib=val_item,
                        assignment=create_assignment(
                            path=[],
                            value=new_value[index],
                            tolerance=tolerance)
                    ))
            self._inverse_assign_multiple_quibs(quib_changes, on_drag=True)

    def _connect_callbacks(self, widget: Union[QSlider, QRangeSlider]):
        widget.on_changed(lambda new_value: self._on_change_slider(new_value, widget))

        # on_release is now disabled. it causes the overriding dialog to appear twice.
        # and it leads to two evaluations of randomization (e.g., in the dice demo).
        widget.on_release = self._on_release
