from typing import Callable, Tuple, Any, Mapping, Set, Optional

import numpy as np

from pyquibbler.assignment import AssignmentToQuib, AssignmentWithTolerance, get_axes_x_y_tolerance
from pyquibbler.function_definitions import KeywordArgument
from pyquibbler.graphics import GraphicsCollection
from pyquibbler.graphics.widgets import QRectangleSelector
from pyquibbler.quib.quib import Quib
from pyquibbler.path import PathComponent
from pyquibbler.debug_utils import timeit
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
        from pyquibbler.quib.quib import Quib
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

            tolerance_x, tolerance_y = get_axes_x_y_tolerance(self._get_axis())
            tolerance = None if tolerance_x is None else np.array([tolerance_x, tolerance_x, tolerance_y, tolerance_y])

            if isinstance(init_val, Quib):
                self._inverse_assign(init_val,
                                     [PathComponent(component=slice(None, None, None),
                                                    indexed_cls=np.ndarray)],
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

    def _run_single_call(self, func: Callable, graphics_collection: GraphicsCollection,
                         args: Tuple[Any, ...], kwargs: Mapping[str, Any], quibs_allowed_to_access: Set[Quib]):
        previous_widgets = graphics_collection.widgets

        # speed-up by changing the current widget instead of creating a new one:
        if len(previous_widgets) == 1:
            previous_widget = list(previous_widgets)[0]

            # TODO: generalize to cases where other kwargs, not just 'extents', are also quibs
            if isinstance(previous_widget, QRectangleSelector) \
                    and len(self.parameter_source_locations) == 1 \
                    and self.parameter_source_locations[0].argument == KeywordArgument(keyword='extents') \
                    and self.parameter_source_locations[0].path == []:
                previous_widget.set_extents_without_callback(self.func_args_kwargs.get('extents').get_value())

                return previous_widget

        return super()._run_single_call(func, graphics_collection, args, kwargs, quibs_allowed_to_access)
