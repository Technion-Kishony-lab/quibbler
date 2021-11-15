from dataclasses import dataclass, field
from typing import Set


@dataclass
class GraphicsCollection:
    widgets: Set = field(default_factory=set)
    artists: Set = field(default_factory=set)
