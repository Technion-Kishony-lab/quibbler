from typing import Iterable


class SettableCycle:
    """
    An iterator that cycles over another iterator and allows setting the iteration index.
    """

    def __init__(self, iterable: Iterable):
        self._iterator = iter(iterable)
        self._is_stop_iteration = False
        self._list = []
        self.current_index = -1

    def __iter__(self):
        return self

    def __next__(self):
        self.current_index += 1
        while len(self._list) <= self.current_index and not self._is_stop_iteration:
            try:
                item = next(self._iterator)
                self._list.append(item)
            except StopIteration:
                self._is_stop_iteration = True

        self.current_index %= len(self._list)

        return self._list[self.current_index]
