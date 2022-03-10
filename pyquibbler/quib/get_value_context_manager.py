from contextlib import contextmanager

IS_WITHIN_GET_VALUE_CONTEXT = False


@contextmanager
def get_value_context():
    """
    Change IS_WITHIN_GET_VALUE_CONTEXT while in the process of running get_value.
    This has to be a static method as the IS_WITHIN_GET_VALUE_CONTEXT is a global state for all quib types
    """
    global IS_WITHIN_GET_VALUE_CONTEXT
    if IS_WITHIN_GET_VALUE_CONTEXT:
        yield
    else:
        IS_WITHIN_GET_VALUE_CONTEXT = True
        try:
            yield
        finally:
            IS_WITHIN_GET_VALUE_CONTEXT = False


def is_within_get_value_context() -> bool:
    return IS_WITHIN_GET_VALUE_CONTEXT
