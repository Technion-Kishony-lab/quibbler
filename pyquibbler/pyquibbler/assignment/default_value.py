from pyquibbler.utilities.basic_types import Singleton


class Default(Singleton):
    """
    A default value for reverting overriding assignments.

    `default` is a singleton instance which is used as value in quib assignments to indicate
    reseting the quib's value back to its default functional value (namely, overruling prior overriding assignments).

    Examples
    --------
    >>> n = iquib(7)
    >>> x = np.arange(n).setp(allow_overriding=True)
    >>> x.get_value()
    array([ 0, 1, 2, 3, 4, 5,  6])
    >>>
    >>> x[1:-1] = 100  # override functional values
    >>> x.get_value()
    array([ 0, 100, 100, 100, 100, 100,  6])
    >>>
    >>> x[2:-2] = default  # set specified elements back to default
    >>> x.get_value()
    array([ 0, 100, 2, 3, 4, 100,  6])
    >>>
    >>> x.assign(default)  # reset all the array back to default
    >>> x.get_value()
    array([ 0, 1, 2, 3, 4, 5,  6])
    """

    def __repr__(self):
        return 'default'


default = Default()
