from typing import Optional

import numpy as np

from pyquibbler.debug_utils import timeit

from pyquibbler.quib.quib import Quib

from pyquibbler.assignment import AssignmentToQuib, AssignmentWithTolerance, get_axes_x_y_tolerance
from pyquibbler.graphics.widgets import QRectangleSelector
from pyquibbler.path import PathComponent

from .widget_call import WidgetQuibFuncCall


class RectangleSelectorQuibFuncCall(WidgetQuibFuncCall):

    @staticmethod
    def _get_control_variable() -> Optional[str]:
        return 'extents'

    def _set_rightclick_callback(self, widget: QRectangleSelector):
        # unlike other widgets, rectangle_selector does take a whole axes for itself.
        # Instead, we set the widget's artists for right-click callback.
        picker_artists = widget._center_handle.artists  # can add here the corners if we want
        for picker_artist in picker_artists:
            picker_artist.set_picker(True)
            picker_artist._quibbler_on_rightclick = self._on_right_click

    def _widget_is_attempting_to_resize_when_not_allowed(self, extents):
        """
        There is a bug in the matplotlib widget that causes it to sometimes give incorrect extents,
        and attempt to resize even when the user did not request to resize- we here check if the widget attempted to
        resize when it should not have been able to
        """
        init_val = self.func_args_kwargs.get('extents')
        allow_resize = self.func_args_kwargs.get('allow_resize')
        if isinstance(init_val, Quib):
            previous_value = init_val.get_value()
        else:
            previous_value = self.run([[]]).extents

        return not allow_resize and (
                previous_value[1] - previous_value[0] != extents[1] - extents[0] or
                previous_value[3] - previous_value[2] != extents[3] - extents[2]
        )

    def _on_changed(self, extents):
        init_val = self.func_args_kwargs.get('extents')

        if self._widget_is_attempting_to_resize_when_not_allowed(extents):
            return

        with timeit("selector_change", "selector change"):

            tolerance = get_axes_x_y_tolerance(self._get_axis())
            tolerance = np.array([tolerance.x, tolerance.x, tolerance.y, tolerance.y]) if tolerance else None

            if isinstance(init_val, Quib):
                self._inverse_assign(init_val,
                                     [PathComponent(slice(None, None, None))],
                                     extents,
                                     tolerance=tolerance,
                                     on_drag=True)
            elif len(init_val) == 4:
                quib_changes = list()
                for index, init_val_item in enumerate(init_val):
                    if isinstance(init_val_item, Quib):
                        quib_changes.append(AssignmentToQuib(
                            quib=init_val_item,
                            assignment=AssignmentWithTolerance.from_value_path_tolerance(
                                path=[],
                                value=extents[index],
                                tolerance=tolerance[index])
                        ))
                self._inverse_assign_multiple_quibs(quib_changes, on_drag=True)

    def _connect_callbacks(self, widget: QRectangleSelector):
        widget.changed_callback = self._on_changed
        widget.release_callback = self._on_release
