


def get_quibs_which_can_change(self):
    """
    Return a list of quibs that can potentially change as a result of the transpositional function- this does NOT
    necessarily mean these quibs will in fact be changed.

    For example, in `np.repeat(q1, q2)`, where q1 is a numpy array quib
    and q2 is a number quib with amount of times to repeat, q2 cannot in any
    situation be changed by a change in `np.repeat`'s result. So only `q1` would be returned.
    """
    from pyquibbler.quib import Quib
    potentially_changed_quib_indices = self.SUPPORTED_FUNCTIONS_TO_POTENTIALLY_CHANGED_QUIB_INDICES[self._func]
    quibs = []
    for i, arg in enumerate(self._args):
        if i in potentially_changed_quib_indices:
            quibs.extend(iter_objects_of_type_in_object_shallowly(Quib, arg))
    return quibs
