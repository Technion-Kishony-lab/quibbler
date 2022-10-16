from pyquibbler import iquib, CacheStatus


def test_list_addition():
    a = iquib([10, 20, 30])
    b = (a + [40, 50]).setp(cache_mode='on')
    b0 = b[0]
    b1 = b[1]
    b2 = b[2]

    b0.get_value()
    b1.get_value()
    b2.get_value()

    assert b.get_value() == [10, 20, 30, 40, 50]
    a[1] = 21
    assert b.get_value() == [10, 21, 30, 40, 50]

    assert b0.cache_status == CacheStatus.ALL_VALID
    assert b1.cache_status == CacheStatus.ALL_INVALID
    assert b2.cache_status == CacheStatus.ALL_VALID


def test_list_multiplication():
    a = iquib([10, 20, 30])
    n = iquib(3)
    b = (n * a).setp(cache_mode='on')

    assert b.get_value() == [10, 20, 30, 10, 20, 30, 10, 20, 30]

    b0 = b[0]
    b1 = b[1]
    b4 = b[4]

    b0.get_value()
    b1.get_value()
    b4.get_value()

    a[1] = 21
    assert b.get_value() == [10, 21, 30, 10, 21, 30, 10, 21, 30]

    assert b0.cache_status == CacheStatus.ALL_VALID
    assert b1.cache_status == CacheStatus.ALL_INVALID
    assert b4.cache_status == CacheStatus.ALL_INVALID
