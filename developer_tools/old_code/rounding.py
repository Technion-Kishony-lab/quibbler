import numpy as np

TYPE_TO_NUMBER_DIGITS = dict()


def get_number_of_digits(value):
    type_ = type(value)
    if type_ not in TYPE_TO_NUMBER_DIGITS:

        eps = type_(1)
        while 1 + eps > 1:
            eps = type_(eps / 10)
        TYPE_TO_NUMBER_DIGITS[type_] = -np.log10(eps)

    return TYPE_TO_NUMBER_DIGITS[type_]

