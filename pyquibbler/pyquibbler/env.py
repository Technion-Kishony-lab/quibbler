from pyquibbler.utilities.basic_types import Flag, Mutable


""" Debug """

DEBUG = Flag(False)

LOG_TO_STDOUT = Flag(False)

LOG_TO_FILE = Flag(False)

END_DRAG_IMMEDIATELY = Flag(False)  # Useful when debugging graphics inverse assignment

SHOW_QUIB_EXCEPTIONS_AS_QUIB_TRACEBACKS = Flag(True)

SAFE_MODE = Flag(True)  # Catch and properly ignore path translation and inversion exceptions.

""" Lazy """

LAZY = Flag(True)

GRAPHICS_LAZY = Flag(False)


""" Quib creation """

ALLOW_ARRAY_WITH_DTYPE_OBJECT = Flag(False)

""" Graphics """

DRAGGABLE_PLOTS_BY_DEFAULT = Flag(True)

GRAPHICS_DRIVEN_ASSIGNMENT_RESOLUTION = Mutable(1000)  # Number of pixels in mouse events. None for infinity

WARN_ON_UNSUPPORTED_BACKEND = Flag(True)


""" Override dialog """

OVERRIDE_DIALOG_IN_SEPARATE_WINDOW = Flag(False)

OVERRIDE_DIALOG_AS_TEXT_FOR_GRAPHICS_ASSIGNMENT = Flag(False)

OVERRIDE_DIALOG_AS_TEXT_FOR_NON_GRAPHICS_ASSIGNMENT = Flag(True)


""" repr """

SHOW_QUIBS_AS_WIDGETS_IN_JUPYTER_LAB = Flag(True)

PRETTY_REPR = Flag(True)

REPR_RETURNS_SHORT_NAME = Flag(False)

REPR_WITH_OVERRIDES = Flag(True)

GET_VARIABLE_NAMES = Flag(True)


""" non-quiby functions """

LEN_BOOL_ETC_RAISE_EXCEPTION = Flag(True)

ITER_RAISE_EXCEPTION = Flag(False)

UNPACKER_CAN_GET_LEN = Flag(True)

""" Others """

INPUT_AWARE_INVERSION = Flag(True)
