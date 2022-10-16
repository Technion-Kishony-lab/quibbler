from pyquibbler import iquib, CacheStatus


def test_list_addition():
    a = iquib([0, 1, 2])
    b = (a + [3, 4]).setp(cache_mode='on')
    b0 = b[0]
    b1 = b[1]
    b2 = b[2]

    b0.get_value()
    b1.get_value()
    b2.get_value()

    assert b.get_value() == [0, 1, 2, 3, 4]
    a[1] = 11
    assert b.get_value() == [0, 11, 2, 3, 4]

    assert b0.cache_status == CacheStatus.ALL_VALID
    assert b1.cache_status == CacheStatus.ALL_INVALID
    assert b2.cache_status == CacheStatus.ALL_VALID
