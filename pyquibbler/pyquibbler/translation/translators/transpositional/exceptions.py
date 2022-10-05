from pyquibbler.exceptions import PyQuibblerException


class PyQuibblerRaggedArrayException(PyQuibblerException):
    def __str__(self):
        return 'Arrays of ragged arrays or lists are not supported.'
