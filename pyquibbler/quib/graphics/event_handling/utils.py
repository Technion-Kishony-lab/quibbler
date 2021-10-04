from __future__ import annotations
from typing import Any, Iterable, TYPE_CHECKING

if TYPE_CHECKING:
    from pyquibbler.quib import Quib


def assign_data(quib: Quib, indices: Any, data_to_set: Any):
    """
    Assign data to a given quib, with measures such as automatically setting the data as a global override if the quib
    is not an iterable, and not assigning anything if the data is None
    """
    # We want to support both single values and arrays, so we need to reverse assign appropriately (not use index
    # if it was a single number)
    indices = indices if isinstance(quib.get_value(), Iterable) else None
    quib.assign(data_to_set, indices=indices)
