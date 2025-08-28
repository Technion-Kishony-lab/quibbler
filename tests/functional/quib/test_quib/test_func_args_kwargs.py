from pyquibbler.function_definitions import FuncArgsKwargs


def dummy_func(a, b, c=3, d=4):
    return a + b + c + d


def test_func_args_kwargs():
    func_args_kwargs = FuncArgsKwargs(dummy_func, (1, 2), {'c': 7})
    assert list(func_args_kwargs.iter_args_and_names_in_function_call(include_defaults=False)) == [
        ('a', 1), ('b', 2), ('c', 7)]

    assert list(func_args_kwargs.iter_args_and_names_in_function_call(include_defaults=True)) == [
        ('a', 1), ('b', 2), ('c', 7), ('d', 4)]

    func_args_kwargs = FuncArgsKwargs(dummy_func, (1,), {'b':2, 'c': 7})
    assert list(func_args_kwargs.iter_args_and_names_in_function_call(include_defaults=False)) == [
        ('a', 1), ('b', 2), ('c', 7)]

    assert list(func_args_kwargs.iter_args_and_names_in_function_call(include_defaults=True)) == [
        ('a', 1), ('b', 2), ('c', 7), ('d', 4)]
