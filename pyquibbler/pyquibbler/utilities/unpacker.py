from dataclasses import dataclass
from inspect import currentframe
from opcode import opname
from typing import Any, Optional

from pyquibbler.env import UNPACKER_CAN_GET_LEN
from pyquibbler.exceptions import PyQuibblerException


@dataclass
class CannotDetermineNumberOfIterations(PyQuibblerException):
    indexed_object: Any

    def __str__(self):
        return f'Cannot determine unpacking amount for {self.indexed_object}.\n' \
               f'Try specifying the desired amount, using Quib.iter_first(amount).'


def get_unpack_amount(frame: Optional = None, raise_if_no_unpack=False) -> Optional[int]:
    """
    Try to determine if the given frame is currently trying to unpack the object in the top of the stack.
    If so, try to determine the expected amount of items to unpack and return that number.
    When frame is not given, the default frame is that of the caller of the caller of this function.
    Return None if no unpacking is found.
    Inspiration - https://stackoverflow.com/a/16481975/2907819
    """
    if frame is None:
        frame = currentframe().f_back.f_back
    if frame is None:
        return None
    bytecode = frame.f_code.co_code
    instruction_index = frame.f_lasti
    instruction = opname[bytecode[instruction_index]]
    if instruction == 'UNPACK_SEQUENCE':
        return bytecode[instruction_index + 1]
    return None


class Unpacker:
    """
    A utility that allows iteration over an object (self._indexable) by using __getitem__ on it with an increasing
    index, until a specific maximum index (self._amount) is reached.
    If the amount is not given by the user, it will be determined automatically.
    """

    def __init__(self, indexable: Any, amount: Optional[int] = None):
        self._indexable = indexable
        self._amount = amount
        self._index = 0
        self._last_caller_info = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._amount is None:
            caller_frame = currentframe().f_back
            caller_instruction = caller_frame.f_lasti
            if self._last_caller_info is not None:
                last_caller_frame, last_caller_instruction = self._last_caller_info
                if caller_frame is last_caller_frame and caller_instruction == last_caller_instruction:
                    if UNPACKER_CAN_GET_LEN:
                        from pyquibbler.quib.quib import Quib
                        try:
                            if isinstance(self._indexable, Quib):
                                self._amount = len(self._indexable.get_value_valid_at_path(None))
                            else:
                                self._amount = len(self._indexable)
                        except TypeError:
                            raise CannotDetermineNumberOfIterations(self._indexable)
                    else:
                        # If next is called on us consecutively from the same bytecode,
                        # we are not going to learn any new information about the unpacking amount,
                        # so we just quit and raise
                        raise CannotDetermineNumberOfIterations(self._indexable)

            self._last_caller_info = caller_frame, caller_instruction
            unpack_amount = get_unpack_amount()
            if unpack_amount is not None:
                self._amount = unpack_amount + self._index

        if self._amount is not None and self._index >= self._amount:
            raise StopIteration
        try:
            item = self._indexable[self._index]
        except IndexError as e:
            raise StopIteration from e
        self._index += 1
        return item
