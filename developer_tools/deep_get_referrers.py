import gc
from typing import Optional


def deep_get_referrers(obj, depth: int, number_sequence=None):
    if obj is None:
        return
    if depth < 0:
        return
    number_sequence = number_sequence or []
    refs = gc.get_referrers(obj)
    for num, ref in enumerate(refs):
        current_number_sequence = [*number_sequence, num]
        print(f'SEQ={current_number_sequence}: TYPE={type(ref)}', ref, end='\n\n')
        deep_get_referrers(ref, depth-1, current_number_sequence)
