DEBUG = False
LAZY = True


def set_debug(debug):
    global DEBUG
    DEBUG = debug


def is_debug():
    return DEBUG


def is_lazy():
    return LAZY
