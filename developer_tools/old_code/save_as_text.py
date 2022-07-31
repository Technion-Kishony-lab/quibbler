import numpy as np


# TODO: at the end we are not using the functions below for array saving. can be deleted

def count_digits(array: np.ndarray):
    """
    returns the max number of digits before and after the decimal point in the entire array.
    """

    max_before = 0
    max_after = 0

    def count(x):
        nonlocal max_before, max_after

        s = str(x)
        d = s.find('.')
        if d >= 0:
            before = d
            after = len(s) - d - 1
        else:
            before = len(s)
            after = 0

        max_before = max(max_before, before)
        max_after = max(max_after, after)

    np.vectorize(count)(array)
    return max_before, max_after


def save_array_as_text(file_path: str, value):
    max_before, max_after = count_digits(value)
    np.savetxt(file_path, value, fmt=f'%{max_before + max_after + 1}.{max_after}f')


FIRST_LINE_OF_FORMATTED_TXT_FILE = '# Formatted Quibbler value file (keep this note)'
