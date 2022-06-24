import contextlib

WITHIN_DRAG_COUNT = 0
WITHIN_RELEASE_COUNT = 0
IS_PRESSED = False


def is_within_release():
    return WITHIN_RELEASE_COUNT > 0


def is_within_drag():
    return WITHIN_DRAG_COUNT > 0 and not is_within_release()


def enter_dragging():
    global WITHIN_DRAG_COUNT
    WITHIN_DRAG_COUNT += 1


def exit_dragging():
    global WITHIN_DRAG_COUNT
    WITHIN_DRAG_COUNT -= 1


def enter_releasing():
    global WITHIN_RELEASE_COUNT
    WITHIN_RELEASE_COUNT += 1


def exist_releasing():
    global WITHIN_RELEASE_COUNT
    WITHIN_RELEASE_COUNT -= 1


@contextlib.contextmanager
def dragging():
    enter_dragging()
    yield
    exit_dragging()


@contextlib.contextmanager
def releasing():
    enter_releasing()
    yield
    exist_releasing()


def pressed():
    global IS_PRESSED
    IS_PRESSED = True


def released():
    global IS_PRESSED
    IS_PRESSED = False


def is_pressed() -> bool:
    global IS_PRESSED
    return IS_PRESSED
