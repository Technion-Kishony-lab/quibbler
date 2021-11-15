from .graphics_function_quib import GraphicsFunctionQuib


class PlotGraphicsFunctionQuib(GraphicsFunctionQuib):
    """
    Made to add the _index_in_plot attribute to plot artists.
    """

    def _call_func(self, *args, **kwargs):
        func_res = super()._call_func(*args, **kwargs)
        for i, artist in enumerate(func_res):
            artist._index_in_plot = i
        return func_res
