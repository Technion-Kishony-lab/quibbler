from .widget_graphics_function_quib import WidgetGraphicsFunctionQuib


class RectangleSelectorGraphicsFunctionQuib(WidgetGraphicsFunctionQuib):
    """
    A quib representing a rectangle selector. Will automatically add a listener and update the relevant quib
    """

    @property
    def extents_quib(self):
        return self.kwargs['extents']
