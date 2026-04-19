from typing import Any


class Number:
    """Representation of a real-valued number."""

    def __init__(self, value: int | float | str, decimal_separator: str = ".") -> None:
        """Store internal value and decimal separator.

        If an empty string is passed, it is represented as zero.

        Args:
            value (int | float | str): Value of number.
            decimal_separator (`str`, optional): Separator for splitting integer part from fractional part.
        """
        self._value: float = self._to_float(value)
        self._separator: str = decimal_separator

    @staticmethod
    def _to_float(value: int | float | str) -> float:
        """Convert arbitrary value to floating number."""
        if isinstance(value, str):
            value = value.replace(",", ".")
        return float(value) if value else 0.0

    def __eq__(self, other: Any) -> bool:
        """Compare number with other object.

        Args:
            other (Any): Object to be compared.

        Returns:
            bool: `True` if object is equal to number, `False` otherwise.
        """
        return self._value == self._to_float(other)

    def __int__(self) -> int:
        """Return integer representation of number.

        Returns:
            int: Number with integer part only.
        """
        return int(self._value)

    def __float__(self) -> float:
        """Return floating point representation of number.

        Returns:
            float: Number with integer and fractional part.
        """
        return self._value

    def __str__(self) -> str:
        """Return string representation of number.

        If the number is zero, an empty string is returned.

        Returns:
            str: Integer including fractional part and corresponding decimal separator if available.
        """
        if not self._value:
            return ""
        if self._value % 1 == 0:
            return str(int(self._value))
        return str(self._value).replace(".", self._separator)
