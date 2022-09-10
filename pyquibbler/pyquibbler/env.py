from pyquibbler.utilities.basic_types import Flag, Mutable

DEBUG = Flag(False)

LAZY = Flag(True)

GRAPHICS_LAZY = Flag(False)

PLOT_WITH_PICKER_TRUE_BY_DEFAULT = Flag(True)

# Effective number of pixels in mouse events. None for infinity
GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION = Mutable(1000)

OVERRIDE_DIALOG_IN_SEPARATE_WINDOW = Flag(False)

OVERRIDE_DIALOG_AS_TEXT_FOR_GRAPHICS_ASSIGNMENT = Flag(False)

OVERRIDE_DIALOG_AS_TEXT_FOR_NON_GRAPHICS_ASSIGNMENT = Flag(True)

# Can be useful when debugging graphics inverse assignment
END_DRAG_IMMEDIATELY = Flag(False)

PRETTY_REPR = Flag(True)

REPR_RETURNS_SHORT_NAME = Flag(False)

REPR_WITH_OVERRIDES = Flag(True)

GET_VARIABLE_NAMES = Flag(True)

LEN_RAISE_EXCEPTION = Flag(True)

BOOL_RAISE_EXCEPTION = Flag(False)

ITER_RAISE_EXCEPTION = Flag(False)

LOG_TO_STDOUT = Flag(False)

LOG_TO_FILE = Flag(False)

SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS = Flag(True)

WARN_ON_UNSUPPORTED_BACKEND = Flag(True)
