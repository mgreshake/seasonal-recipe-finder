from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from PyQt6.QtWidgets import QFrame

from widgets import Widget


class Line(Widget, ABC):
    """Interface for simple line."""

    def __init__(self, length: int, parent: Window | None = None, linewidth: int = 1) -> None:
        """Wrap frame from PyQt into separate object.

        Args:
            length (int): Line length in pixels.
            parent (`Window`, optional): Window containing line.
            linewidth (`int`, optional): Line width in pixels. Defaults to 1 pixel.
        """
        self._instance: QFrame = QFrame(parent and parent._instance)
        super().__init__(self._instance)

        self.draw(length)

        self._instance.setLineWidth(linewidth)

    @property
    def linewidth(self) -> int:
        """int: Line width in pixels."""
        return self._instance.lineWidth()

    @abstractmethod
    def draw(self, length: int) -> None:
        ...


class HorizontalLine(Line):
    """Interface for horizontal line."""

    def __init__(self, length: int, *args: Any, **kwargs: Any) -> None:
        """Create PyQt Frame with horizontal line shape.

        Args:
            length (int): Line length in pixels.
            *args (Any): Argument list for base line.
            **kwargs (Any): Keyword arguments for base line.
        """
        super().__init__(length, *args, **kwargs)

    @property
    def length(self) -> int:
        """int: Line length in pixels."""
        return self._instance.width()

    def draw(self, length: int) -> None:
        """Draw horizontal length of given length."""
        self._instance.setFrameShape(QFrame.Shape.HLine)
        self._instance.setFixedWidth(length)


class VerticalLine(Line):
    """Interface for vertical line."""

    def __init__(self, length: int, *args: Any, **kwargs: Any) -> None:
        """Create PyQt Frame with vertical line shape.

        Args:
            length (int): Line length in pixels.
            *args (Any): Argument list for base line.
            **kwargs (Any): Keyword arguments for base line.
        """
        super().__init__(length, *args, **kwargs)

    @property
    def length(self) -> int:
        """int: Line length in pixels."""
        return self._instance.height()

    def draw(self, length: int) -> None:
        """Draw vertical line of given length."""
        self._instance.setFrameShape(QFrame.Shape.VLine)
        self._instance.setFixedHeight(length)


class EmptySpace(Widget):
    """Interface for empty space."""

    def __init__(self, parent: Window | None = None, width: int | None = None, height: int | None = None) -> None:
        """Create PyQt Frame with no shape.

        Args:
            parent (`Window`, optional): Window containing space.
            width (`int`, optional): Width in pixels. Default depends on window size.
            height (`int`, optional): Height in pixels. Default depends on window size.
        """
        self._instance: QFrame = QFrame(parent and parent._instance)
        super().__init__(self._instance, width, height)
