from pyquibbler.utils import Flag

DEBUG = Flag(True)

EVALUATE_NOW = Flag(False)

GRAPHICS_EVALUATE_NOW = Flag(True)

# Assignment restrictions are incomplete at the moment -
# they consider changes to the same quib contradictory, while
# only changes to the same paths should be.
ASSIGNMENT_RESTRICTIONS = Flag(False)

OVERIDE_DIALOG_IN_SEPERATE_WINDOW = Flag(False)

# Can be useful when debugging graphics inverse assignment
END_DRAG_IMMEDIATELY = Flag(False)

PRETTY_REPR = Flag(True)

REPR_RETURNS_SHORT_NAME = Flag(False)

REPR_WITH_OVERRIDES = Flag(True)

GET_VARIABLE_NAMES = Flag(True)

LEN_RAISE_EXCEPTION = Flag(True)

LOG_TO_STDOUT = Flag(False)

SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS = Flag(True)
