from typing import Callable, Tuple, Any, Mapping, Set

from matplotlib.widgets import AxesWidget

from pyquibbler.graphics.graphics_collection import GraphicsCollection
from pyquibbler.quib import Quib
from pyquibbler.quib.function_running import FunctionRunner


class WidgetRunner(FunctionRunner):

    def _connect_callbacks(self, widget: AxesWidget):
        """
        Add any logic here for connecting callbacks to your widget
        """
        pass

    def _run_single_call(self, func: Callable, graphics_collection: GraphicsCollection,
                         args: Tuple[Any, ...], kwargs: Mapping[str, Any], quibs_allowed_to_access: Set[Quib]):
        previous_widgets = graphics_collection.widgets
        res = super(WidgetRunner, self)._run_single_call(func, graphics_collection, args, kwargs, quibs_allowed_to_access)

        # We don't want to recreate the widget every time (and re-add callbacks)- if we already had a widget, just
        # return that
        if len(previous_widgets) > 0 and isinstance(res, AxesWidget):
            assert len(previous_widgets) == 1
            res = list(previous_widgets)[0]
        else:
            # This widget never existed- we're creating it for the first time, so we need to connect callbacks
            self._connect_callbacks(res)

        return res
