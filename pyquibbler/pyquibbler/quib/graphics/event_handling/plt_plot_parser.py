from __future__ import annotations

from typing import Any, Tuple, List, Optional

from pyquibbler.utilities.general_utils import Args
from pyquibbler.utilities.numpy_original_functions import np_shape


ArgIndices = List[Optional[int]]


def _is_arg_str(arg):
    from pyquibbler.quib.quib import Quib
    if isinstance(arg, Quib):
        arg = arg.get_value()
    return isinstance(arg, str)


def get_xdata_arg_indices_and_ydata_arg_indices(args: Args) -> Tuple[ArgIndices, ArgIndices, ArgIndices]:
    """
    Gets three same-length lists of indices of arguments referencing `xdata` and `ydata` and 'fmt' of a plot command

    xdata indices and fmt indices can be None

    There are a few options for how arguments can be built for plot

    A. (ydata)
    B. (ydata, fmt, ...)
    C. (xdata, ydata, ...)
    D. (xdata, ydata, fmt, ...)
    """

    x_data_arg_indices = []
    y_data_arg_indices = []
    fmt_indices = []

    # We have `self` (Axes) as arg 0
    i = 1

    while i < len(args):
        number_of_remaining_args = len(args) - i
        i0, i1, i2 = i, i + 1, i + 2
        if number_of_remaining_args == 1:
            # ydata
            xyf_indices = None, i0, None
            i += 1
        elif _is_arg_str(args[i1]):
            # ydata, fmt
            xyf_indices = None, i0, i1
            i += 2
        elif number_of_remaining_args == 2 or not _is_arg_str(args[i2]):
            # xdata, ydata
            xyf_indices = i0, i1, None
            i += 2
        else:
            # xdata, ydata, fmt
            xyf_indices = i0, i1, i2
            i += 3

        x_data_arg_indices.append(xyf_indices[0])
        y_data_arg_indices.append(xyf_indices[1])
        fmt_indices.append(xyf_indices[2])

    return x_data_arg_indices, y_data_arg_indices, fmt_indices


def _get_number_of_columns(arg: Any):
    """
    Return size at axis=1. if less than 2 dimensions, return 1.
    This is the number of artists produced by plot for this arg.
    """
    from pyquibbler.quib.quib import Quib
    if isinstance(arg, Quib):
        shape = arg.get_shape()
    else:
        shape = np_shape(arg)
    if len(shape) < 2:
        return 1
    return shape[1]


def get_data_number_and_index_from_artist_index(args: Args, x_data_arg_indices, y_data_arg_indices, artist_index: int
                                                ) -> Tuple[int, int]:
    """
    Returns the x-y pair number (data_number) and their column (data_column) that correspond to a given artist_index
    produced by a plt.plot command.

    plt.plot(x0, y0, [fmt], x1, y1, [fmt], ...)

    x0, y0 are data_number=0
    x1, y1 are data_number=1
    etc

    for example,
    plt.plot(x34, y34, 'o', x7, y7, 'x', x52, y5, '.', x41, y47)
    where x34 is an array of shape = (3, 4)

    will create a list of 4 + 1 + 2 + 7 = 14 artists
    artist_index = 9 will yield:
        data_number = 3 (namely, x41, y47)
        column_index = 2 (it is created by the data in the column 2 of x41, y47. x is broadcasted)
    """
    data_number = -1
    total_number_of_artists = 0
    while artist_index >= total_number_of_artists:
        data_number += 1
        y_index = y_data_arg_indices[data_number]
        num_columns_y = _get_number_of_columns(args[y_index])
        x_index = x_data_arg_indices[data_number]
        if x_index is None:
            num_artists = num_columns_y
        else:
            num_columns_x = _get_number_of_columns(args[x_index])
            num_artists = num_columns_x if num_columns_y == 1 else num_columns_y  # broadcast
        total_number_of_artists += num_artists
    column_index = artist_index - (total_number_of_artists - num_artists)
    return data_number, column_index
