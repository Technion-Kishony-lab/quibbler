from typing import Optional, Callable

from matplotlib.axes._base import _process_plot_var_args


class quibbler_process_plot_var_args(_process_plot_var_args):
    """
    make _idx a property to be able to set a callback on it
    """
    callback: Optional[Callable] = None

    @property
    def _idx(self):
        return self.__idx

    @_idx.setter
    def _idx(self, value):
        if self.callback:
            self.callback(self, self.__idx)
        self.__idx = value
