from enum import Enum


class UpdateType(str, Enum):

    DRAG = 'drag'
    DROP = 'drop'
    CENTRAL = 'central'
    NEVER = 'never'
