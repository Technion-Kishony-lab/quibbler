from pyquibbler.utils import Singleton


class Missing(Singleton):
    """
    Designates a missing value in a function call
    """

    def __repr__(self):
        return 'missing'


missing = Missing()
