from dataclasses import dataclass
from typing import Set

from matplotlib.artist import Artist
from matplotlib.widgets import AxesWidget


@dataclass
class GraphicsCollection:

    widgets: Set
    artists: Set
