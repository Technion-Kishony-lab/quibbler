from pyquibbler import iquib


def test_list_addition_inversal():
    a = iquib([0, 1, 2])
    b = iquib([3, 4])
    ab = a + b

    assert ab.get_value() == [0, 1, 2, 3, 4]
    ab[1] = 11

    assert a.get_value() == [0, 11, 2]
    assert ab.get_value() == [0, 11, 2, 3, 4]

