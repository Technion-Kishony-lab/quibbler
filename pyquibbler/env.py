from .utils import Flag

DEBUG = Flag(True)

LAZY = Flag(True)

# Assignment restrictions are incomplete at the moment -
# they consider changes to the same quib contradictory, while
# only changes to the same paths should be.
ASSIGNMENT_RESTRICTIONS = Flag(False)

# Can be useful when debugging graphics inverse assignment
END_DRAG_IMMEDIATELY = Flag(False)

PRETTY_REPR = Flag(False)
