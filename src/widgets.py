from __future__ import annotations

from abc import ABC
from collections.abc import Callable, Iterable
from typing import Any, NamedTuple, TypeAlias, TypeVar

from PyQt6.QtCore import QEvent, QItemSelectionModel, QModelIndex, QRegularExpression, QSortFilterProxyModel, Qt
from PyQt6.QtGui import QIcon, QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QCompleter,
    QFrame,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QPushButton,
    QStyle,
)

from utils.collections import ListEntries, ListEntry, LiteralDict


_WidgetT = TypeVar("_WidgetT", bound=QComboBox | QFrame | QLabel | QLineEdit | QListWidget | QTextEdit | QPushButton)


Command: TypeAlias = Callable[..., None]


ALIGNMENTS: LiteralDict[Qt.AlignmentFlag] = LiteralDict({
    "left": Qt.AlignmentFlag.AlignLeft,
    "center": Qt.AlignmentFlag.AlignHCenter,
    "right": Qt.AlignmentFlag.AlignRight,
})

INPUT_POLICY: LiteralDict[str] = LiteralDict({
    "word": r"[^\W\d]+",
    "number": r"[-+]?(\d+[\.,]?|\d*[\.,]\d+)",
    "integer": r"[-+]?\d+",
    "decimal": r"[-+]?(\d+[\.,]|\d*[\.,]\d+)",
    "count": r"[1-9]\d*",
})


class Size(NamedTuple):
    width: int
    height: int


class Widget(ABC):
    """Interface for arbitrary GUI widget."""

    def __init__(self, widget: _WidgetT, width: int | None = None, height: int | None = None) -> None:
        """Wrap widget from PyQt into separate object.

        Args:
            widget (_WidgetT): Widget to be wrapped.
            width (`int`, optional): Width in pixels. Default depends on content and window size.
            height (`int`, optional): Height in pixels. Default depends on content and window size.
        """
        self._instance: _WidgetT = widget

        if width is not None:
            self._instance.setFixedWidth(width)
        if height is not None:
            self._instance.setFixedHeight(height)

    @property
    def size(self) -> Size:
        """Size: Width and height in pixels."""
        return Size(self._instance.width(), self._instance.height())


class Label(Widget):
    """Interface for GUI label."""

    def __init__(
        self,
        text: str,
        parent: Window | None = None,
        alignment: str = "left",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create PyQt label with text.

        Args:
            text (str): Label content.
            parent (`Window`, optional): Window containing label.
            alignment (`str`, optional): Alignment of label content. Possible options are `left`, `right` and `center`.
                Defaults to `left`.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.
        """
        self._instance: QLabel = QLabel(text, parent and parent._instance)
        super().__init__(self._instance, *args, **kwargs)

        self._alignment: str = alignment

        self._instance.setAlignment(self._instance.alignment() | ALIGNMENTS[self._alignment])
        self._instance.setWordWrap(True)

    @property
    def text(self) -> str:
        """str: Label content."""
        return self._instance.text()

    @property
    def alignment(self) -> str:
        """str: Alignment of label content."""
        return self._alignment


class Icon(Widget):
    """Interface for pixel map."""

    def __init__(self, source: str | int, parent: Window | None = None, *args: Any, **kwargs: Any) -> None:
        """Create PyQt label with pixel map.

        Args:
            source (str | int): Image path or enum of standard pixel map.
            parent (`Window`, optional): Window containing icon.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.

        Raises:
            TypeError: If source type is not supported.
            ValueError: If image path or standard pixel map are invalid.
        """
        self._instance: QLabel = QLabel(parent and parent._instance)
        super().__init__(self._instance, *args, **kwargs)

        match source:
            case str():
                icon = QIcon(source)
            case int():
                icon = QApplication.style().standardIcon(QStyle.StandardPixmap(source))
            case _:
                data_type = type(source).__name__
                raise TypeError(f"Unknown source type found: {data_type}. Must be image path or standard pixel map.")

        if icon.isNull():
            raise ValueError(f"Invalid source found: {source}")

        self._instance.setPixmap(icon.pixmap(*self.size))


class Button(Widget):
    """Interface for clickable button."""

    def __init__(
        self,
        label: str | Icon,
        parent: Window | None = None,
        callback: Command | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create PyQt button and assigns trigger callback.

        Args:
            label (str | Icon): Either text or icon as button label.
            parent (`Window`, optional): Window containing button.
            callback (`Command`, optional): Callback that triggers when button is clicked.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.
        """
        text = label if isinstance(label, str) else ""
        icon = QIcon(label._instance.pixmap()) if isinstance(label, Icon) else QIcon()

        self._instance: QPushButton = QPushButton(icon, text, parent and parent._instance)
        super().__init__(self._instance, *args, **kwargs)

        self._label: str | Icon = label

        if callback is not None:
            self._instance.clicked.connect(callback)

    @property
    def label(self) -> str | Icon:
        """str | Icon: Button label."""
        return self._label

    def click(self) -> None:
        """Perform click on button."""
        self._instance.click()


class TextField(Widget):
    """Interface for single-line text input."""

    def __init__(
        self,
        parent: Window | None = None,
        text: str = "",
        alignment: str = "left",
        policy: str | None = None,
        callback: Command | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create PyQt single-line text edit.

        Args:
            parent (`Window`, optional): Window containing text field.
            text (`str`, optional): Initial content. Defaults to no content.
            alignment (`str`, optional): Alignment of text input. Possible options are 'left', 'right' and 'center'.
                Defaults to 'left'.
            policy (`str`, optional): Policy defining which input is acceptable. Possible options are `text`, `number`,
                `integer` and `decimal`. All inputs are accepted by default.
            callback (`Command`, optional): Callback that triggers when input changes.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.
        """
        self._instance: QLineEdit = QLineEdit(text, parent and parent._instance)
        super().__init__(self._instance, *args, **kwargs)

        self._alignment: str = alignment

        self._instance.setAlignment(ALIGNMENTS[self._alignment])

        if policy is not None:
            expression = QRegularExpression(INPUT_POLICY[policy])
            input_validator = QRegularExpressionValidator(expression)
            self._instance.setValidator(input_validator)

        if callback is not None:
            self._instance.textEdited[str].connect(callback)

    @property
    def content(self) -> str:
        """str: Current content."""
        return self._instance.text()

    @property
    def alignment(self) -> str:
        """str: Alignment of text input."""
        return self._alignment

    def has_valid_content(self) -> bool:
        """Check if content fulfills input policy if available.

        If no policy is set, every content is accepted.

        Returns:
            bool: `True` if content is valid, `False` otherwise.
        """
        return self._instance.hasAcceptableInput()

    def fill(self, text: str) -> None:
        """Insert text into text field.

        Args:
            text (str): Text to be inserted.
        """
        self._instance.setText(text)
        self._instance.textEdited[str].emit(text)


class TextBox(Widget):
    """Interface for multi-line text input."""

    def __init__(
        self,
        parent: Window | None = None,
        text: str = "",
        alignment: str = "left",
        is_editable: bool = True,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create PyQt text edit.

        Args:
            parent (`Window`, optional): Window containing text box.
            text (`str`, optional): Initial content. Defaults to no content.
            alignment (`str`, optional): Alignment of text input. Possible options are 'left', 'right' and 'center'.
                Defaults to 'left'.
            is_editable (`bool`, optional): Flag whether text box is editable. Defaults to `True`.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.
        """
        self._instance: QTextEdit = QTextEdit(text, parent and parent._instance)
        super().__init__(self._instance, *args, **kwargs)

        self._alignment: str = alignment

        self._instance.setAlignment(ALIGNMENTS[self._alignment])

        if not is_editable:
            self._instance.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

    @property
    def content(self) -> str:
        """str: Current content."""
        return self._instance.toPlainText()

    @property
    def alignment(self) -> str:
        """str: Alignment of text input."""
        return self._alignment

    @property
    def is_editable(self) -> bool:
        """bool: `True` if text box is editable, `False` otherwise."""
        return self._instance.textInteractionFlags() == Qt.TextInteractionFlag.TextEditorInteraction

    def fill(self, text: str) -> None:
        """Insert text into text box.

        Args:
            text (str): Text to be inserted.
        """
        self._instance.setText(text)


class ListBox(Widget):
    """Interface for GUI list."""

    def __init__(
        self,
        parent: Window | None = None,
        entries: Iterable[Any] = (),
        default_index: int = -1,
        callback: Command | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create PyQt list with entries.

        Args:
            entries (`Iterable[Any]`, optional): List entries consisting of labels and data if available. Default are no
                entries.
            parent (`Window`, optional): Window containing list box.
            default_index (`int`, optional): Index of entry selected by default. Defaults to no entry.
            callback (`Command`, optional): Callback that triggers when entry is selected.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.
        """
        self._instance: _QToggleListWidget = _QToggleListWidget(parent and parent._instance)
        super().__init__(self._instance, *args, **kwargs)

        self.entries: ListEntries = entries

        self._instance.setCurrentRow(default_index)
        self._instance.selectionModel().selectionChanged.connect(self.on_selection_changed)

        if callback is not None:
            self._instance.currentRowChanged[int].connect(callback)

    @property
    def entries(self) -> ListEntries[Any]:
        """ListEntries[Any]: Current list entries."""
        return ListEntries([
            (self._instance.item(index).text(), self._instance.item(index).data(Qt.ItemDataRole.UserRole))
            for index in range(self._instance.count())
        ])

    @entries.setter
    def entries(self, values: Iterable[Any]) -> None:
        self._instance.clear()
        for entry in ListEntries(values):
            self.append(entry)

    @property
    def count(self) -> int:
        """int: Number of entries."""
        return self._instance.count()

    @property
    def selected_index(self) -> int:
        """int: Index of currently selected entry. Return `-1` if no entry is selected."""
        return self._instance.currentRow()

    @property
    def selected_entry(self) -> ListEntry[Any] | None:
        """ListEntry[Any] | None: Currently selected entry if available."""
        entry = self._instance.currentItem()
        return entry and ListEntry((entry.text(), entry.data(Qt.ItemDataRole.UserRole)))

    def is_empty(self) -> bool:
        """Check if list box contains entries.

        Returns:
            bool: `True` if list box is empty, `False` otherwise.
        """
        return self._instance.count() == 0

    def select(self, index: int) -> None:
        """Select specified entry in list box.

        If the index is less than zero, the selection remains empty.

        Args:
            index (int): Index of entry to be selected.

        Raises:
            IndexError: If index is greater than or equal to number of entries.
        """
        if index >= self._instance.count():
            raise IndexError(f"Entry with index {index} does not exist")
        self._instance.setCurrentRow(index)

    def deselect(self) -> None:
        """Deselect current entry in list box."""
        self._instance.setCurrentRow(-1)

    def append(self, entry: tuple) -> None:
        """Append new entry to list box.

        Args:
            entry (tuple[str, Any]): Entry to be appended.
        """
        item = QListWidgetItem(entry[0])
        item.setData(Qt.ItemDataRole.UserRole, entry[1])
        self._instance.addItem(item)

    def insert(self, index: int, entry: tuple) -> None:
        """Insert new entry at specified position in list box.

        Args:
            index (int): Index at which new entry is inserted.
            entry (tuple[str, Any]): Entry to be inserted.

        Raises:
            IndexError: If invalid index is passed.
        """
        if 0 > index or index > self._instance.count():
            raise IndexError(f"Entry cannot be inserted at index {index}")
        item = QListWidgetItem(entry[0])
        item.setData(Qt.ItemDataRole.UserRole, entry[1])
        self._instance.insertItem(index, item)

    def remove(self, index: int) -> None:
        """Remove specified entry from list box.

        Args:
            index (int): Index of entry to be removed.

        Raises:
            IndexError: If invalid index is passed.
        """
        if 0 > index or index >= self._instance.count():
            raise IndexError(f"Entry with index {index} does not exist")
        self._instance.takeItem(index)

    def update(self, index: int, entry: tuple) -> None:
        """Update specified entry in list box.

        Args:
            index (int): Index of entry to be updated.
            entry (tuple[str, Any]): New content of specified entry.

        Raises:
            IndexError: If invalid index is passed.
        """
        if 0 > index or index >= self._instance.count():
            raise IndexError(f"Entry with index {index} does not exist")
        self._instance.item(index).setText(entry[0])
        self._instance.item(index).setData(Qt.ItemDataRole.UserRole, entry[1])

    def clear(self) -> None:
        """Remove all entries from list box."""
        self._instance.clear()

    def on_selection_changed(self) -> None:
        """Release current entry when nothing is selected."""
        if not self._instance.selectionModel().selectedIndexes():
            self._instance.setCurrentRow(-1)


class _QToggleListWidget(QListWidget):
    """PyQt list widget that deselects current item when clicked again."""

    def selectionCommand(self, index: QModelIndex, event: QEvent | None = None) -> QItemSelectionModel.SelectionFlag:
        if event and event.type() == event.Type.MouseButtonPress and event.button() == Qt.MouseButton.LeftButton:
            if self.selectionModel().isSelected(index):
                return QItemSelectionModel.SelectionFlag.Deselect
            return QItemSelectionModel.SelectionFlag.ClearAndSelect
        return super().selectionCommand(index, event)


class DropdownList(Widget):
    """Interface for collapsible list."""

    def __init__(
        self,
        entries: Iterable[Any],
        parent: Window | None = None,
        default_index: int = 0,
        callback: Command | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create PyQt combo box with entries.

        Args:
            entries (Iterable[Any]): List entries consisting of labels and data if available.
            parent (`Window`, optional): Window containing dropdown list.
            default_index (`int`, optional): Index of entry selected by default. Defaults to first entry.
            callback (`Command`, optional): Callback that triggers when entry is selected.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.
        """
        self._instance: QComboBox = QComboBox(parent and parent._instance)
        super().__init__(self._instance, *args, **kwargs)

        self.entries: ListEntries = entries

        self._instance.setCurrentIndex(default_index)

        if callback is not None:
            self._instance.currentIndexChanged[int].connect(callback)

    @property
    def entries(self) -> ListEntries[Any]:
        """ListEntries[Any]: Available list entries."""
        return ListEntries([
            (self._instance.itemText(index), self._instance.itemData(index))
            for index in range(self._instance.count())
        ])

    @entries.setter
    def entries(self, values: Iterable[Any]) -> None:
        self._instance.clear()
        for text, data in ListEntries(values):
            self._instance.addItem(text, data)

    @property
    def selected_index(self) -> int:
        """int: Index of currently selected entry. Return `-1` if no entry is selected."""
        return self._instance.currentIndex()

    @property
    def selected_entry(self) -> ListEntry[Any]:
        """ListEntry[Any]: Currently selected entry if available."""
        return ListEntry((self._instance.currentText(), self._instance.currentData()))

    def select(self, index: int) -> None:
        """Set selection of dropdown list.

        If the index is less than zero, the selection remains empty.

        Args:
            index (int): Index of entry to be selected.

        Raises:
            IndexError: If index is greater than or equal to number of entries.
        """
        if index >= self._instance.count():
            raise IndexError(f"Entry with index {index} does not exist")
        self._instance.setCurrentIndex(index)


class ComboBox(DropdownList):
    """Interface for collapsible list that is searchable."""

    def __init__(
        self,
        entries: Iterable[Any],
        parent: Window | None = None,
        text_input: str = "",
        default_index: int = -1,
        max_num_entries: int = 10,
        callback: Command | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Create searchable PyQt combo box with entries.

        Args:
            entries (Iterable[Any]): List entries consisting of labels and data if available.
            parent (`Window`, optional): Window containing combo box.
            text_input (`str`, optional): Initial content of text field. Defaults to no content.
            default_index (`int`, optional): Index of entry selected by default. Defaults to no entry. Only applies if
                no text is passed.
            max_num_entries (`int`, optional): Maximum number of visible entries. Defaults to 10.
            callback (`Command`, optional): Callback that triggers when entry is selected.
            *args (`Any`, optional): Argument list for base widget.
            **kwargs (`Any`, optional): Keyword arguments for base widget.
        """
        self._text_field: TextField = TextField(parent, callback=self.on_text_field_edited)

        super().__init__(entries, parent, -1 if text_input else default_index, callback, *args, **kwargs)

        self._instance.setEditable(True)
        self._instance.setEditText(text_input or self._instance.currentText())
        self._instance.setLineEdit(self._text_field._instance)

        self._filter_model: QSortFilterProxyModel = QSortFilterProxyModel(self._instance)
        self._filter_model.setFilterCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self._filter_model.setSourceModel(self._instance.model())

        self._completer: QCompleter = QCompleter(self._filter_model, self._instance)
        self._completer.setCompletionMode(QCompleter.CompletionMode.UnfilteredPopupCompletion)

        self._instance.setCompleter(self._completer)
        self._instance.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self._instance.setMaxVisibleItems(max_num_entries)

        self._completer.activated[str].connect(self.on_completer_activated)

    @property
    def text_field(self) -> TextField:
        """TextField: Text field with current content."""
        return self._text_field

    @property
    def max_num_entries(self) -> int:
        """int: Maximum number of entries displayed on screen."""
        return self._instance.maxVisibleItems()

    def select(self, index: int) -> None:
        """Set selection of combo box.

        If the index is less than zero, the selection remains empty. The number of available entries may be reduced
        depending on the text input.

        Args:
            index (int): Index of filtered entry to be selected.

        Raises:
            IndexError: If index is greater than or equal to number of filtered entries.
        """
        if index >= self._completer.model().rowCount():
            raise IndexError(f"Entry with index {index} does not exist")
        text = self._completer.model().index(index, 0).data()
        self._completer.activated[str].emit(text)

    def on_text_field_edited(self, text: str) -> None:
        """Update current selection and filter entries of completion model.

        Args:
            text (str): Current text input.
        """
        index = self._instance.findText(text)
        self._instance.setCurrentIndex(index)
        self._instance.setCurrentText(text)
        self._filter_model.setFilterFixedString(text)

    def on_completer_activated(self, text: str) -> None:
        """Submit selected entry from completion model if available.

        Args:
            text (str): Label of selected entry.
        """
        if text:
            index = self._instance.findText(text)
            self._instance.setCurrentIndex(index)
            self._instance.activated[int].emit(index)
