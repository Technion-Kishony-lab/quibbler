from pyquibbler.exceptions import PyQuibblerException


class CannotCalculateShapeException(PyQuibblerException):

    def __str__(self):
        return "Could not run np.shape on the result"
