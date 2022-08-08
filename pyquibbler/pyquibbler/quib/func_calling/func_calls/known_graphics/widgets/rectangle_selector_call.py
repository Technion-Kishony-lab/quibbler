from typing import Callable, Tuple, Any, Mapping, Set

import numpy as np

from pyquibbler.assignment import AssignmentToQuib
from pyquibbler.assignment.assignment import AssignmentWithTolerance
from pyquibbler.env import GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
from pyquibbler.function_definitions import KeywordArgument
from pyquibbler.graphics import releasing, GraphicsCollection
from pyquibbler.graphics.widgets import QRectangleSelector
from pyquibbler.quib import Quib
from pyquibbler.logger import logger
from .widget_call import WidgetQuibFuncCall
from pyquibbler.path import PathComponent


class RectangleSelectorQuibFuncCall(WidgetQuibFuncCall):

    def _widget_is_attempting_to_resize_when_not_allowed(self, extents):
        """
        There is a bug in the matplotlib widget that causes it to sometimes give incorrect extents,
        and attempt to resize even when the user did not request to resize- we here check if the widget attempted to
        resize when it should not have been able to
        """
        from pyquibbler.quib import Quib
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

        from pyquibbler import timer
        from pyquibbler.quib import Quib

        ax = self._get_axis()
        if GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION is None:
            tolerance = None
        else:
            tolerance_x = (ax.get_xlim()[1] - ax.get_xlim()[0]) / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
            tolerance_y = (ax.get_ylim()[1] - ax.get_ylim()[0]) / GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION
            tolerance = np.array([tolerance_x, tolerance_x, tolerance_y, tolerance_y])

        if isinstance(init_val, Quib):
            with timer("selector_change", lambda x: logger.info(f"selector change {x}")):
                if self._widget_is_attempting_to_resize_when_not_allowed(extents):
                    return
                self._inverse_assign(init_val,
                                     [PathComponent(component=slice(None, None, None),
                                                    indexed_cls=np.ndarray)],
                                     extents,
                                     tolerance=tolerance)
        elif len(init_val) == 4:
            quib_changes = list()
            for index, init_val_item in enumerate(init_val):
                if isinstance(init_val_item, Quib):
                    quib_changes.append(AssignmentToQuib(quib=init_val_item,
                                                         assignment=AssignmentWithTolerance
                                                         (path=[],
                                                          value=extents[index],
                                                          value_up=extents[index] + tolerance[index],
                                                          value_down=extents[index] - tolerance[index]
                                                          )))
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
