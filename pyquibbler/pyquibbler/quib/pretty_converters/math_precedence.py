import enum


class MathPrecedence(enum.IntEnum):
    VAR_NAME = 20
    PARENTHESIS = 19
    FUNCTION_CALL = 18
    SLICING = 17
    SUBSCRIPTION = 16
    ATTRIBUTE = 15
    EXPONENTIATION = 14
    BITWISE_NOT = 13
    POSNEG = 12
    MULDIV = 11
    ADDSUB = 10
    BITWISE_SHIFT = 9
    BITWISE_AND = 8
    BITWISE_XOR = 7
    BITWISE_OR = 6
    COMPARISON = 5
    BOOL_NOT = 4
    BOOL_AND = 3
    BOOL_OR = 2
    LAMBDA = 1
    VAR_NAME_WITH_SPACES = 0
