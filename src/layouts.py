from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, NamedTuple, TypeAlias, TypeVar

from PyQt6.QtCore import QMargins
from PyQt6.QtWidgets import QBoxLayout, QFormLayout, QHBoxLayout, QVBoxLayout

from widgets import ALIGNMENTS, Label, Widget


_LayoutT = TypeVar("_LayoutT", bound=QBoxLayout | QFormLayout)


class Margins(NamedTuple):
    left: int = 0
    top: int = 0
    right: int = 0
    bottom: int = 0

    @classmethod
    def from_object(cls, margins: QMargins) -> Margins:
        """Initialize tuple from PyQt margins object.

        Args:
            margins (QMargins): PyQt margins object.

        Returns:
            Margins: Tuple containing margins.
        """
        return cls(margins.left(), margins.top(), margins.right(), margins.bottom())


class Layout(ABC):
    """Interface for arbitrary GUI layout."""

    def __init__(self, layout: _LayoutT, spacing: int = 6, margins: Margins = Margins()) -> None:
        """Wrap layout from PyQt into separate object.

        Args:
            layout (_LayoutT): Layout to be wrapped.
            spacing (`int`, optional): Spacing between layout items in pixels. Defaults to 6 pixels.
            margins (`Margins`, optional): Margins in pixels. Defaults to 11 pixels in all directions.
        """
        self._instance: _LayoutT = layout
        self._items: list[LayoutItem | list[LayoutItem]] = []

        self._instance.setSpacing(spacing)
        self._instance.setContentsMargins(*margins)

    def __getitem__(self, position: int) -> LayoutItem | list[LayoutItem]:
        """Return item at specified position.

        Args:
            position (int): Position of item within layout.

        Returns:
            LayoutItem | list[LayoutItem]: Item at requested position.
        """
        return self._items[position]

    @property
    def spacing(self) -> int:
        """int: Spacing between layout items in pixels."""
        return self._instance.spacing()

    @property
    def margins(self) -> Margins:
        """Margins: Margins in pixels."""
        return Margins.from_object(self._instance.contentsMargins())

    @abstractmethod
    def add_item(self, *args: Any) -> None:
        ...


LayoutItem: TypeAlias = Widget | Layout | tuple[Label, Widget | Layout]


class BoxLayout(Layout, ABC):
    """Interface for GUI layout that appends widgets."""

    def __init__(self, layout: QBoxLayout, alignment: str = "left", *args: Any, **kwargs: Any) -> None:
        """Wrap box layout from PyQt into separate object.

        Args:
            layout (QBoxLayout): Layout to be wrapped.
            alignment (`str`, optional): Alignment of layout items. Possible options are `left`, `right` and `center`.
                Defaults to `left`.
            *args (Any): Argument list for base layout.
            **kwargs (Any): Keyword arguments for base layout.
        """
        super().__init__(layout, *args, **kwargs)

        self._alignment: str = alignment
        self._instance.setAlignment(ALIGNMENTS[self._alignment])

    @property
    def alignment(self) -> str:
        """str: Alignment of layout items."""
        return self._alignment

    def add_item(self, item: Widget | Layout) -> None:
        """Add widget or nested layout to layout.

        Args:
            item (Widget | Layout): Item to be added.

        Raises:
            TypeError: If item to be added is neither widget nor layout.
        """
        match item:
            case Widget():
                self._instance.addWidget(item._instance, alignment=ALIGNMENTS[self._alignment])
            case Layout():
                self._instance.addLayout(item._instance)
            case _:
                raise TypeError(f"Invalid item type found: {type(item).__name__}. Must be 'Widget' or 'Layout'.")

        self._items.append(item)


class HorizontalBoxLayout(BoxLayout):
    """Interface for GUI layout that arranges widgets horizontally."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize horizontal box layout from PyQt.

        Args:
            *args (Any): Argument list for box layout.
            **kwargs (Any): Keyword arguments for box layout.
        """
        self._instance: QHBoxLayout = QHBoxLayout()
        super().__init__(self._instance, *args, **kwargs)


class VerticalBoxLayout(BoxLayout):
    """Interface for GUI layout that arranges widgets vertically."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize vertical box layout from PyQt.

        Args:
            *args (Any): Argument list for box layout.
            **kwargs (Any): Keyword arguments for box layout.
        """
        self._instance: QVBoxLayout = QVBoxLayout()
        super().__init__(self._instance, *args, **kwargs)


class FormLayout(Layout):
    """Interface for GUI layout that arranges widgets as form with associated label."""

    def __init__(
        self,
        alignment: str = "left",
        horizontal_spacing: int = 6,
        vertical_spacing: int = 6,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialize form layout from PyQt.

        Args:
            alignment (`str`, optional): Alignment of form. Possible options are `left`, `right` and `center`. Defaults
                to `left`.
            horizontal_spacing (`int`, optional): Spacing between items and associated labels in pixels. Default is 6
                pixels.
            vertical_spacing (`int`, optional): Spacing between rows in pixels. Defaults to 6 pixels.
            *args (Any): Argument list for base layout.
            **kwargs (Any): Keyword arguments for base layout.
        """
        self._instance: QFormLayout = QFormLayout()
        super().__init__(self._instance, *args, **kwargs)

        self._alignment: str = alignment

        self._instance.setFormAlignment(ALIGNMENTS[alignment])
        self._instance.setHorizontalSpacing(horizontal_spacing)
        self._instance.setVerticalSpacing(vertical_spacing)

    @property
    def alignment(self) -> str:
        """str: Alignment of form."""
        return self._alignment

    @property
    def horizontal_spacing(self) -> int:
        """int: Spacing between items and associated labels in pixels."""
        return self._instance.horizontalSpacing()

    @property
    def vertical_spacing(self) -> int:
        """int: Spacing between rows in pixels."""
        return self._instance.verticalSpacing()

    def add_item(self, label: Label, item: Widget | Layout) -> None:
        """Add widget or nested layout and associated label to layout.

        Args:
            label (Label): Associated label.
            item (Widget | Layout): Item to be added.
        """
        self._items.append((label, item))
        self._instance.addRow(label._instance, item._instance)
