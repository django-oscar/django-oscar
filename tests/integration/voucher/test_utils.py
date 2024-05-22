from oscar.apps.voucher.utils import generate_code


def test_generate_code():
    result = generate_code(length=16)
    assert len(result) == 19
    assert result.count("-") == 3

    result = generate_code(length=16, group_length=3)
    assert len(result) == 21
    assert result.count("-") == 5

    result = generate_code(length=16, group_length=3, separator="_")
    assert len(result) == 21
    assert result.count("_") == 5

    result = generate_code(length=16, group_length=16, separator=" ")
    assert len(result) == 16
    assert result.count(" ") == 0
