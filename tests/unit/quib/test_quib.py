from pytest import fixture

from pyquibbler.quib import Quib


class ExampleQuib(Quib):
    def __init__(self, artists_redrawers, children, value):
        super().__init__(artists_redrawers, children)
        self.value = value

    def _invalidate(self):
        pass

    def get_value(self):
        return self.value


@fixture
def example_quib():
    return ExampleQuib(set(), [], ['the', 'quib', 'value'])


def test_quib_getitem(example_quib):
    got = example_quib[0]
    assert isinstance(got, Quib)
    assert got.get_value() is example_quib.value[0]


def test_quib_getattr(example_quib):
    got = example_quib.sort
    assert isinstance(got, Quib)
    assert got.get_value() == example_quib.value.sort

def test_quib_call():
    expected_args = (2, 'args')
    expected_kwargs = dict(name='val')
    expected_result = 'the result'
    def wrapped_func(*args, **kwargs):
        assert expected_args == args
        assert expected_kwargs == kwargs
        return expected_result
    quib = ExampleQuib(set(), [], wrapped_func)
    call_quib = quib(*expected_args, **expected_kwargs)
    result = call_quib.get_value()

    assert result is expected_result
