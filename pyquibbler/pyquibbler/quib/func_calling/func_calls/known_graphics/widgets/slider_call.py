from typing import Optional

from pyquibbler.assignment import AssignmentToQuib, create_assignment
from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
from pyquibbler.graphics.widgets import QSlider, QRangeSlider
from pyquibbler.path import PathComponent
from pyquibbler.quib.func_calling.func_calls.known_graphics.widgets.widget_call import WidgetQuibFuncCall
from pyquibbler.quib.quib import Quib


class SliderQuibFuncCall(WidgetQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        return 'valinit'

    def _get_tolerance(self, widget):
        """
        we only need to apply tolerance if the widget does not specify a `valstep`
        """
        if widget.valstep is None and GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val is not None:
            return (widget.valmax - widget.valmin) / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION.val
        return None

    def _on_change_slider(self, new_value, widget: QSlider):
        val = self.func_args_kwargs.get(self._get_control_variable())
        if isinstance(val, Quib):
            self._inverse_assign(val, [], new_value, tolerance=self._get_tolerance(widget), on_drag=True)

    def _connect_callbacks(self, widget: QSlider):
        widget.on_changed(lambda new_value: self._on_change_slider(new_value, widget))

        # on_release is now disabled. it causes the overriding dialog to appear twice.
        # and it leads to two evaluations of randomization (e.g., in the dice demo).
        widget.on_release = self._on_release


class RangeSliderQuibFuncCall(SliderQuibFuncCall):

    def _on_change_slider(self, new_value, widget: QRangeSlider):
        val = self.func_args_kwargs.get(self._get_control_variable())
        quib_changes = list()
        if isinstance(val, Quib):
            for index in range(2):
                quib_changes.append(AssignmentToQuib(
                    quib=val,
                    assignment=create_assignment(path=[PathComponent(index)],
                                                 value=new_value[index],
                                                 tolerance=self._get_tolerance(widget))
                ))
        else:
            for index, val_item in enumerate(val):
                if isinstance(val_item, Quib):
                    quib_changes.append(AssignmentToQuib(
                        quib=val_item,
                        assignment=create_assignment(path=[],
                                                     value=new_value[index],
                                                     tolerance=self._get_tolerance(widget))
                    ))
        self._inverse_assign_multiple_quibs(quib_changes, on_drag=True)
