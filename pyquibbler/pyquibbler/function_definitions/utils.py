import functools
import inspect

from .types import PositionalArgument, KeywordArgument


@functools.lru_cache()
def get_signature_for_func(func):
    """
    Get the signature for a function- the reason we use this instead of immediately going to inspect is in order to
    cache the result per function
    """
    return inspect.signature(func)


def get_parameters_for_func(func):
    try:
        sig = get_signature_for_func(func)
        return sig.parameters
    except (ValueError, TypeError):
        return {}


@functools.lru_cache()
def get_positional_to_keyword_arguments(func):
    return {
        PositionalArgument(i): KeywordArgument(name) if parameter.kind.name != "POSITIONAL_ONLY" else None
        for i, (name, parameter) in enumerate(get_parameters_for_func(func).items())
    }


@functools.lru_cache()
def get_keyword_to_positional_arguments(func):
    return {
        KeywordArgument(name): PositionalArgument(i) if parameter.kind.name != "KEYWORD_ONLY" else None
        for i, (name, parameter) in enumerate(get_parameters_for_func(func).items())
    }


def get_corresponding_argument(func, argument):
    """
    Get the argument of the opposite type (positional v keyword) which corresponds to the same argument

    For example, given:

    def my_func(a):
        pass

    `a` could be referenced by both PositionalArgument(0) or KeywordArgument("a")

    In this instance:
        If given PositionalArgument(0) will return KeywordArgument("a")
        If given KeywordArgument("a") will return PositionalArgument(0)
    """
    if isinstance(argument, PositionalArgument):
        corresponding_dict = get_positional_to_keyword_arguments(func)
    elif isinstance(argument, KeywordArgument):
        corresponding_dict = get_keyword_to_positional_arguments(func)
    else:
        assert False
    return corresponding_dict.get(argument, None)
