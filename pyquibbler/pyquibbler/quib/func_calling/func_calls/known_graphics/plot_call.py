from pyquibbler.path.path_component import Path
from pyquibbler.quib.func_calling import CachedQuibFuncCall


class PlotQuibFuncCall(CachedQuibFuncCall):

    def _run_on_path(self, valid_path: Path):
        res = super(PlotQuibFuncCall, self)._run_on_path(valid_path)
        graphics_collection = self.graphics_collections[()]
        for i, artist in enumerate(graphics_collection.artists):
            artist._index_in_plot = i

        return res
