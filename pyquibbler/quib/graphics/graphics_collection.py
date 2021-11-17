from dataclasses import dataclass, field
from typing import List


@dataclass
class GraphicsCollection:
    widgets: List = field(default_factory=list)
    artists: List = field(default_factory=list)
