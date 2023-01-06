from pyquibbler import iquib, quiby, q, is_quiby, Quib

not_quib = iquib(3)
not_quiby_str = quiby(str)
not_quib_str_3 = q(str, 3)


def test_iquib_does_not_create_quib_when_uninitiated():
    quib = iquib(3)
    assert isinstance(quib, Quib) and quib.get_value() == 3, "sanity"
    assert not isinstance(not_quib, Quib) and not_quib == 3


def test_quiby_does_not_create_quiby_func_when_uninitiated():
    quiby_str = quiby(str)
    assert is_quiby(quiby_str), "sanity"
    assert not is_quiby(not_quiby_str)


def test_q_does_not_create_quib_when_uninitiated():
    quib_str_3 = q(str, 3)
    assert isinstance(quib_str_3, Quib) and quib_str_3.get_value() == '3'
    assert not isinstance(not_quib_str_3, Quib) and not_quib_str_3 == '3'
