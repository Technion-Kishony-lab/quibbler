from pyquibbler import iquib


def test_list_addition_inversal():
    a = iquib([10, 20, 30])
    b = iquib([40, 50])
    ab = a + b

    assert ab.get_value() == [10, 20, 30, 40, 50]
    ab[1] = 21

    assert a.get_value() == [10, 21, 30]
    assert ab.get_value() == [10, 21, 30, 40, 50]


def test_list_multiplication_inversal():
    a = iquib([10, 20, 30])
    n = iquib(4)
    c = n * a

    assert c.get_value() == 4 * [10, 20, 30]
    c[4] = 100

    assert a.get_value() == [10, 100, 30]
    assert c.get_value() == 4 * [10, 100, 30]
