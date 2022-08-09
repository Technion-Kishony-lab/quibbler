IS_PRESSED = False


def pressed():
    global IS_PRESSED
    IS_PRESSED = True


def released():
    global IS_PRESSED
    IS_PRESSED = False


def is_pressed() -> bool:
    global IS_PRESSED
    return IS_PRESSED
