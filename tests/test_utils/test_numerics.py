import pytest

from utils.numerics import Number


class TestNumber:

    def test_create_number_from_integer(self):
        assert Number(42) == 42
    
    def test_create_number_from_decimal(self):
        assert Number(3.141) == 3.141

    @pytest.mark.parametrize("string, result", [("3.141", 3.141), ("3,141", 3.141), ("", 0.0)])
    def test_create_number_from_string(self, string, result):
        assert Number(string) == result

    @pytest.mark.parametrize("other, result", [(42, True), (42.0, True), ("42", True), ("3,141", False)])
    def test_compare_with_other_number(self, other, result):
        number = Number(42)
        assert (number == other) == result

    def test_return_number_as_integer(self):
        number = Number(3.141)
        assert int(number) == 3

    def test_return_number_as_float(self):
        number = Number(3.141)
        assert float(number) == 3.141

    @pytest.mark.parametrize(
        "value, separator, result",
        [(3.141, ".", "3.141"), (3.141, ",", "3,141"), (42.0, ".", "42"), (0.0, ".", "")],
    )
    def test_return_number_as_string(self, value, separator, result):
        number = Number(value, separator)
        assert str(number) == result
