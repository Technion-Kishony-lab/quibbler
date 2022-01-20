

def test_multiple_quib_save_without_given_name(create_quib_with_return_value):
    example_quib = create_quib_with_return_value(5, allow_overriding=True)
    example_quib.assign_value(10)
    another_quib = create_quib_with_return_value(6).setp(allow_overriding=True)
    another_quib.assign_value(8)

    example_quib.save_if_relevant()
    another_quib.save_if_relevant()
    another_quib.load()
    example_quib.load()

    assert example_quib.get_value() == 10
    assert another_quib.get_value() == 8
