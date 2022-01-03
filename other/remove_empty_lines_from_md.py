import os
import numpy as np


def remove_empty_lines_from_md(filename) -> None:
    file = open(filename, 'r')
    lines = file.readlines()
    file.close()
    l = len(lines)
    i = 0
    dist_from_formatted_line = np.zeros(l)

    file = open(filename, 'w')
    current_dist = -1
    for current_line in lines:
        if current_line.startswith('    '):
            current_dist = 0
        elif current_line == '\n' and current_dist >= 0:
            current_dist += 1
        else:
            current_dist = -1
        if current_dist <= 1:
            file.write(current_line)

    file.close()
    return




