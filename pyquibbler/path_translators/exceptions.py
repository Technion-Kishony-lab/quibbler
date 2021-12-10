from pyquibbler.exceptions import PyQuibblerException


class TranslationException(PyQuibblerException):
    pass


class CannotInvertException(TranslationException):
    pass
