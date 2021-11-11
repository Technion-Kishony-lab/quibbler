import contextlib

WITHIN_DRAG_COUNT = 0


def is_within_drag():
    return WITHIN_DRAG_COUNT > 0


@contextlib.contextmanager
def dragging():
    global WITHIN_DRAG_COUNT
    WITHIN_DRAG_COUNT += 1
    yield
    WITHIN_DRAG_COUNT -= 1
