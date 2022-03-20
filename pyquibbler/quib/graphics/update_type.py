from pyquibbler.utils import StrEnum


class UpdateType(StrEnum):

    DRAG = 'drag'
    DROP = 'drop'
    CENTRAL = 'central'
    NEVER = 'never'
